from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import FileResponse, JsonResponse, StreamingHttpResponse
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import Script, ScriptExecution, AdminFile, ProductWorkflow
import subprocess
import sys
import os
import tempfile
from io import StringIO
import traceback
import time
import json
import threading
import logging

logger = logging.getLogger(__name__)

# Dossier des fichiers par défaut (script data)
SCRIPT_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "script data"
)
DEFAULT_INPUT     = os.path.join(SCRIPT_DATA_DIR, "input.xlsx")
DEFAULT_BACKOFFICE = os.path.join(SCRIPT_DATA_DIR, "databackoffice.csv")
DEFAULT_TRAINING  = os.path.join(SCRIPT_DATA_DIR, "entarinementdataset.csv")


def login_view(request):
    """Login page - no signup allowed"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect')
    
    return render(request, 'scripts/login.html')


def logout_view(request):
    """Logout user"""
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard showing user's scripts"""
    scripts = Script.objects.filter(user=request.user)
    recent_executions = ScriptExecution.objects.filter(user=request.user)[:10]
    
    context = {
        'scripts': scripts,
        'recent_executions': recent_executions,
    }
    return render(request, 'scripts/dashboard.html', context)


@login_required
def script_create(request):
    """Create a new script"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        code = request.POST.get('code', '')
        
        # Parse default variables
        var_names = request.POST.getlist('default_var_name[]')
        default_variables = [name.strip() for name in var_names if name.strip()]
        
        script = Script.objects.create(
            name=name,
            description=description,
            code=code,
            default_variables=default_variables,
            user=request.user
        )
        messages.success(request, 'Script créé avec succès!')
        return redirect('script_detail', pk=script.pk)
    
    return render(request, 'scripts/script_form.html')


@login_required
def script_detail(request, pk):
    """View and edit script details"""
    script = get_object_or_404(Script, pk=pk, user=request.user)
    executions = script.executions.all()[:10]
    
    context = {
        'script': script,
        'executions': executions,
    }
    return render(request, 'scripts/script_detail.html', context)


@login_required
def script_edit(request, pk):
    """Edit script"""
    script = get_object_or_404(Script, pk=pk, user=request.user)
    
    if request.method == 'POST':
        script.name = request.POST.get('name')
        script.description = request.POST.get('description', '')
        script.code = request.POST.get('code', '')
        
        # Parse default variables
        var_names = request.POST.getlist('default_var_name[]')
        script.default_variables = [name.strip() for name in var_names if name.strip()]
        
        script.save()
        messages.success(request, 'Script mis à jour!')
        return redirect('script_detail', pk=script.pk)
    
    context = {'script': script}
    return render(request, 'scripts/script_form.html', context)


@login_required
def script_delete(request, pk):
    """Delete script"""
    script = get_object_or_404(Script, pk=pk, user=request.user)
    
    if request.method == 'POST':
        script.delete()
        messages.success(request, 'Script supprimé!')
        return redirect('dashboard')
    
    return render(request, 'scripts/script_confirm_delete.html', {'script': script})


@login_required
def script_execute(request, pk):
    """Execute a script"""
    script = get_object_or_404(Script, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Parse custom variables
        var_names = request.POST.getlist('var_name[]')
        var_values = request.POST.getlist('var_value[]')
        variables = {}
        for name, value in zip(var_names, var_values):
            if name.strip() and value.strip():  # Only add non-empty variables
                variables[name.strip()] = value.strip()
        
        # Create execution record
        execution = ScriptExecution.objects.create(
            script=script,
            user=request.user,
            status='running',
            variables=variables
        )
        
        # Handle input file if provided
        input_file_path = None
        if 'input_file' in request.FILES:
            input_file = request.FILES['input_file']
            execution.input_file = input_file
            execution.save()
            input_file_path = execution.input_file.path
        
        # Redirect to real-time execution page
        return redirect('execution_realtime', pk=execution.pk)
    
    return render(request, 'scripts/script_execute.html', {'script': script})

@login_required
def execution_realtime(request, pk):
    """Show real-time execution page"""
    execution = get_object_or_404(ScriptExecution, pk=pk, user=request.user)
    return render(request, 'scripts/execution_realtime.html', {'execution': execution})


@login_required
def execution_stream(request, pk):
    """Stream script execution output in real-time"""
    execution = get_object_or_404(ScriptExecution, pk=pk, user=request.user)
    script = execution.script
    
    def generate():
        # Send initial message
        yield f"data: {json.dumps({'type': 'start', 'message': 'Démarrage de l exécution...'})}\n\n"
        time.sleep(0.5)
        
        # Create temporary file for script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_script:
              temp_script.write(script.code)
              temp_script_path = temp_script.name
        
        try:
            # Prepare environment
            env = os.environ.copy()
            if execution.input_file:
                env['INPUT_FILE'] = execution.input_file.path
                yield f"data: {json.dumps({'type': 'log', 'message': f'📁 Fichier d entrée: {execution.get_input_filename()}'})}\n\n"
            
            # Add custom variables to environment
            if execution.variables:
                yield f"data: {json.dumps({'type': 'log', 'message': '🔧 Variables personnalisées:'})}\n\n"
                for var_name, var_value in execution.variables.items():
                    env[var_name] = str(var_value)
                    yield f"data: {json.dumps({'type': 'log', 'message': f'   • {var_name} = {var_value}'})}\n\n"
            
            yield f"data: {json.dumps({'type': 'log', 'message': '▶️  Exécution du script...'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '─' * 60})}\n\n"
            
            # Execute script with real-time output
            env['PYTHONIOENCODING'] = 'utf-8'
            process = subprocess.Popen(
                  [sys.executable, '-u', temp_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env,
                    cwd=os.path.dirname(temp_script_path),
                    bufsize=1
                    )
            
            # Collect all output for saving
            all_output = []
            all_errors = []
            
            # Read output line by line in real-time
            import select
            while True:
                # Check if process is still running
                if process.poll() is not None:
                    # Process finished, read remaining output
                    remaining_out = process.stdout.read()
                    remaining_err = process.stderr.read()
                    
                    if remaining_out:
                        for line in remaining_out.splitlines():
                            if line.strip():
                                all_output.append(line)
                                yield f"data: {json.dumps({'type': 'stdout', 'message': line})}\n\n"
                    
                    if remaining_err:
                        for line in remaining_err.splitlines():
                            if line.strip():
                                all_errors.append(line)
                                yield f"data: {json.dumps({'type': 'stderr', 'message': line})}\n\n"
                    break
                
                # Read available output
                line = process.stdout.readline()
                if line:
                    line = line.rstrip()
                    all_output.append(line)
                    yield f"data: {json.dumps({'type': 'stdout', 'message': line})}\n\n"
                
                # Read available errors
                err_line = process.stderr.readline()
                if err_line:
                    err_line = err_line.rstrip()
                    all_errors.append(err_line)
                    yield f"data: {json.dumps({'type': 'stderr', 'message': err_line})}\n\n"
                
                time.sleep(0.1)
            
            # Get return code
            return_code = process.returncode
            
            yield f"data: {json.dumps({'type': 'log', 'message': '─' * 60})}\n\n"
            
            # Save logs
            logs = ""
            if all_output:
                logs += "STDOUT:\n" + "\n".join(all_output) + "\n\n"
            if all_errors:
                logs += "STDERR:\n" + "\n".join(all_errors)
            
            execution.logs = logs if logs else "Aucune sortie"
            
            # Check for output file
            output_file_path = os.path.join(os.path.dirname(temp_script_path), 'output.xlsx')
            if os.path.exists(output_file_path):
                with open(output_file_path, 'rb') as f:
                    execution.output_file.save('output.xlsx', ContentFile(f.read()))
                os.remove(output_file_path)
                yield f"data: {json.dumps({'type': 'log', 'message': '💾 Fichier de sortie créé'})}\n\n"
            
            # Update status
            if return_code == 0:
                execution.status = 'success'
                yield f"data: {json.dumps({'type': 'success', 'message': '✅ Exécution terminée avec succès!', 'execution_id': execution.pk})}\n\n"
            else:
                execution.status = 'error'
                yield f"data: {json.dumps({'type': 'error', 'message': f'❌ Erreur: Code de retour {return_code}', 'execution_id': execution.pk})}\n\n"
            
            execution.save()
            
        except Exception as e:
            error_msg = f"Erreur d'exécution:\n{traceback.format_exc()}"
            execution.logs = error_msg
            execution.status = 'error'
            execution.save()
            yield f"data: {json.dumps({'type': 'error', 'message': f'❌ Erreur: {str(e)}', 'execution_id': execution.pk})}\n\n"
        
        finally:
            # Clean up
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
    
    response = StreamingHttpResponse(generate(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@login_required
def execution_detail(request, pk):
    """View execution details and logs"""
    execution = get_object_or_404(ScriptExecution, pk=pk, user=request.user)
    
    context = {
        'execution': execution,
    }
    return render(request, 'scripts/execution_detail.html', context)


@login_required
def execution_history(request):
    """View all executions for current user"""
    executions = ScriptExecution.objects.filter(user=request.user)
    
    context = {
        'executions': executions,
    }
    return render(request, 'scripts/execution_history.html', context)


@login_required
def download_file(request, pk, file_type):
    """Download input or output file"""
    execution = get_object_or_404(ScriptExecution, pk=pk, user=request.user)
    
    if file_type == 'input' and execution.input_file:
        return FileResponse(execution.input_file.open('rb'), as_attachment=True)
    elif file_type == 'output' and execution.output_file:
        return FileResponse(execution.output_file.open('rb'), as_attachment=True)
    
    messages.error(request, 'Fichier non trouvé')
    return redirect('execution_detail', pk=pk)


@login_required
def excel_explorer(request):
    """Excel Explorer - View and manipulate Excel files without storage"""
    return render(request, 'scripts/excel_explorer.html')


@login_required
def admin_files(request):
    """Admin Files - Manage project files (models, env, configs)"""
    files = AdminFile.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        file_type = request.POST.get('file_type')
        uploaded_file = request.FILES.get('file')
        
        if name and file_type and uploaded_file:
            admin_file = AdminFile.objects.create(
                name=name,
                description=description,
                file=uploaded_file,
                file_type=file_type,
                uploaded_by=request.user
            )
            messages.success(request, f'Fichier "{name}" importé avec succès')
            return redirect('admin_files')
        else:
            messages.error(request, 'Veuillez remplir tous les champs requis')
    
    context = {
        'files': files,
    }
    return render(request, 'scripts/admin_files.html', context)


@login_required
def admin_file_delete(request, pk):
    """Delete an admin file"""
    admin_file = get_object_or_404(AdminFile, pk=pk)
    filename = admin_file.name
    admin_file.delete()
    messages.success(request, f'Fichier "{filename}" supprimé avec succès')
    return redirect('admin_files')


@login_required
def admin_file_download(request, pk):
    """Download an admin file"""
    admin_file = get_object_or_404(AdminFile, pk=pk)
    return FileResponse(admin_file.file.open('rb'), as_attachment=True)



# =============================================================================
# WORKFLOW PRODUITS — vues
# =============================================================================

@login_required
def workflow_produits(request):
    """Page principale : formulaire d'upload + liste des exécutions."""
    workflows = ProductWorkflow.objects.filter(user=request.user)[:20]

    # Vérification disponibilité des fichiers par défaut
    defaults = {
        "input_ok": os.path.isfile(DEFAULT_INPUT),
        "backoffice_ok": os.path.isfile(DEFAULT_BACKOFFICE),
        "training_ok": os.path.isfile(DEFAULT_TRAINING),
    }

    PIPELINE_STEPS = [
        "Nettoyage + Fusion doublons",
        "1bis Contrôle Qualité",
        "1ter Comparaison Backoffice",
        "1qua Mapping État",
        "2 Correction EAN-13",
        "3 Prédiction ML",
        "4 Textes SEO",
        "5 Prix & SKU",
        "6 Images Bing",
        "7 Export Excel",
    ]

    return render(request, "scripts/workflow_produits.html", {
        "workflows": workflows,
        "defaults": defaults,
        "steps_list": PIPELINE_STEPS,
    })


@login_required
def workflow_produits_run(request):
    """Lance un nouveau workflow produits (POST)."""
    if request.method != "POST":
        return redirect("workflow_produits")

    # Créer l'entrée en base
    wf = ProductWorkflow.objects.create(user=request.user, status="pending", progress=0)

    # Gérer les fichiers : upload utilisateur OU fichier par défaut
    def _sauvegarder_ou_defaut(field_name, default_path, wf_field_attr):
        if field_name in request.FILES:
            f = request.FILES[field_name]
            getattr(wf, wf_field_attr).save(f.name, f, save=False)
            return None  # fichier uploadé, pas besoin de chemin externe
        return default_path  # on utilisera le fichier par défaut sur disque

    chemin_input      = _sauvegarder_ou_defaut("input_file",      DEFAULT_INPUT,      "input_file")
    chemin_backoffice = _sauvegarder_ou_defaut("backoffice_file",  DEFAULT_BACKOFFICE, "backoffice_file")
    chemin_training   = _sauvegarder_ou_defaut("training_file",    DEFAULT_TRAINING,   "training_file")
    wf.save()

    # Résoudre les chemins finals
    def _chemin_final(wf_file_field, default_chemin):
        if wf_file_field and wf_file_field.name:
            return wf_file_field.path
        if default_chemin and os.path.isfile(default_chemin):
            return default_chemin
        return None

    path_input      = _chemin_final(wf.input_file,      chemin_input)
    path_backoffice = _chemin_final(wf.backoffice_file,  chemin_backoffice)
    path_training   = _chemin_final(wf.training_file,    chemin_training)

    # Validation
    manquants = []
    if not path_input:      manquants.append("input.xlsx")
    if not path_backoffice: manquants.append("databackoffice.csv")
    if not path_training:   manquants.append("entarinementdataset.csv")

    if manquants:
        wf.status = "error"
        wf.logs = f"Fichiers manquants : {', '.join(manquants)}"
        wf.save()
        messages.error(request, f"Fichiers manquants : {', '.join(manquants)}")
        return redirect("workflow_produits")

    # Dossier de sortie
    from django.conf import settings
    output_dir = os.path.join(settings.MEDIA_ROOT, "workflow", "outputs", str(wf.pk))

    # Lancer le pipeline dans un thread séparé pour ne pas bloquer Django
    def _run():
        from .product_pipeline import run_pipeline

        logs_lines = []

        def progress_cb(pct, msg):
            wf.progress = pct
            wf.progress_message = msg
            logs_lines.append(f"[{pct:3d}%] {msg}")
            wf.logs = "\n".join(logs_lines)
            ProductWorkflow.objects.filter(pk=wf.pk).update(
                progress=pct, progress_message=msg, logs=wf.logs
            )

        try:
            ProductWorkflow.objects.filter(pk=wf.pk).update(status="running", progress=0)

            pipeline_result = run_pipeline(
                input_path=path_input,
                backoffice_path=path_backoffice,
                training_path=path_training,
                output_dir=output_dir,
                progress_cb=progress_cb,
            )
            output_path          = pipeline_result["output_final"]
            output_erreurs_path  = pipeline_result["output_erreurs"]
            output_dupliques_path = pipeline_result["output_dupliques"]
            output_non_dup_path  = pipeline_result["output_non_dupliques"]

            # Lire le résultat pour compter les lignes
            import pandas as pd
            df_out = pd.read_excel(output_path)
            nb_out = len(df_out)

            # Sauvegarder le fichier de sortie dans Django
            with open(output_path, "rb") as fh:
                wf_db = ProductWorkflow.objects.get(pk=wf.pk)
                wf_db.output_file.save(
                    os.path.basename(output_path), ContentFile(fh.read()), save=False
                )

            # Sauvegarder les fichiers secondaires (erreurs, dupliqués, non-dupliqués)
            def _save_extra(field_name, path):
                if path and os.path.isfile(path):
                    with open(path, "rb") as fh:
                        getattr(wf_db, field_name).save(
                            os.path.basename(path), ContentFile(fh.read()), save=False
                        )

            _save_extra("output_erreurs_file",        output_erreurs_path)
            _save_extra("output_dupliques_file",       output_dupliques_path)
            _save_extra("output_non_dupliques_file",   output_non_dup_path)

            wf_db.status = "success"
            wf_db.progress = 100
            wf_db.nb_lignes_output = nb_out
            wf_db.finished_at = timezone.now()
            wf_db.logs = "\n".join(logs_lines) + f"\n[100%] ✅ {nb_out} produits exportés."
            wf_db.save()
        except Exception as exc:
            err = traceback.format_exc()
            logger.error("Workflow #%s erreur : %s", wf.pk, err)
            ProductWorkflow.objects.filter(pk=wf.pk).update(
                status="error",
                logs="\n".join(logs_lines) + f"\n❌ ERREUR :\n{err}",
                finished_at=timezone.now(),
            )

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    messages.success(request, "Pipeline lancé ! Suivez la progression en temps réel.")
    return redirect("workflow_produits_progress", pk=wf.pk)


@login_required
def workflow_produits_progress(request, pk):
    """Page de suivi en temps réel."""
    wf = get_object_or_404(ProductWorkflow, pk=pk, user=request.user)
    PIPELINE_STEPS = [
        "Nettoyage + Fusion", "1bis Contrôle Qualité", "1ter Backoffice",
        "1qua Mapping État", "2 EAN-13", "3 ML Predict",
        "4 Textes SEO", "5 Prix & SKU", "6 Images Bing", "7 Export Excel",
    ]
    return render(request, "scripts/workflow_progress.html", {
        "wf": wf,
        "steps_list": PIPELINE_STEPS,
    })


@login_required
def workflow_produits_status(request, pk):
    """API JSON de polling pour la progression."""
    wf = get_object_or_404(ProductWorkflow, pk=pk, user=request.user)
    return JsonResponse({
        "status":   wf.status,
        "progress": wf.progress,
        "message":  wf.progress_message,
        "logs":     wf.logs,
        "nb_lignes_output": wf.nb_lignes_output,
        "output_url": (
            wf.output_file.url if wf.output_file and wf.output_file.name else None
        ),
        "output_erreurs_url": (
            wf.output_erreurs_file.url if wf.output_erreurs_file and wf.output_erreurs_file.name else None
        ),
        "output_dupliques_url": (
            wf.output_dupliques_file.url if wf.output_dupliques_file and wf.output_dupliques_file.name else None
        ),
        "output_non_dupliques_url": (
            wf.output_non_dupliques_file.url if wf.output_non_dupliques_file and wf.output_non_dupliques_file.name else None
        ),
    })


@login_required
def workflow_produits_detail(request, pk):
    """Détail d'un workflow terminé."""
    wf = get_object_or_404(ProductWorkflow, pk=pk, user=request.user)
    return render(request, "scripts/workflow_detail.html", {"wf": wf})


@login_required
def workflow_produits_download(request, pk):
    """Téléchargement du fichier Excel résultat."""
    wf = get_object_or_404(ProductWorkflow, pk=pk, user=request.user)
    if not wf.output_file or not wf.output_file.name:
        messages.error(request, "Aucun fichier disponible pour ce workflow.")
        return redirect("workflow_produits_detail", pk=pk)
    return FileResponse(
        wf.output_file.open("rb"),
        as_attachment=True,
        filename=os.path.basename(wf.output_file.name),
    )


@login_required
def workflow_produits_download_erreurs(request, pk):
    """Téléchargement du fichier lignes avec erreurs."""
    wf = get_object_or_404(ProductWorkflow, pk=pk, user=request.user)
    if not wf.output_erreurs_file or not wf.output_erreurs_file.name:
        messages.error(request, "Aucun fichier d'erreurs disponible pour ce workflow.")
        return redirect("workflow_produits_detail", pk=pk)
    return FileResponse(
        wf.output_erreurs_file.open("rb"),
        as_attachment=True,
        filename=os.path.basename(wf.output_erreurs_file.name),
    )


@login_required
def workflow_produits_download_dupliques(request, pk):
    """Téléchargement du fichier produits dupliqués."""
    wf = get_object_or_404(ProductWorkflow, pk=pk, user=request.user)
    if not wf.output_dupliques_file or not wf.output_dupliques_file.name:
        messages.error(request, "Aucun fichier de dupliqués disponible pour ce workflow.")
        return redirect("workflow_produits_detail", pk=pk)
    return FileResponse(
        wf.output_dupliques_file.open("rb"),
        as_attachment=True,
        filename=os.path.basename(wf.output_dupliques_file.name),
    )


@login_required
def workflow_produits_download_non_dupliques(request, pk):
    """Téléchargement du fichier produits non dupliqués."""
    wf = get_object_or_404(ProductWorkflow, pk=pk, user=request.user)
    if not wf.output_non_dupliques_file or not wf.output_non_dupliques_file.name:
        messages.error(request, "Aucun fichier disponible pour ce workflow.")
        return redirect("workflow_produits_detail", pk=pk)
    return FileResponse(
        wf.output_non_dupliques_file.open("rb"),
        as_attachment=True,
        filename=os.path.basename(wf.output_non_dupliques_file.name),
    )


@login_required
def workflow_produits_delete(request, pk):
    """Supprime un workflow."""
    wf = get_object_or_404(ProductWorkflow, pk=pk, user=request.user)
    if request.method == "POST":
        wf.delete()
        messages.success(request, "Workflow supprimé.")
        return redirect("workflow_produits")
    return render(request, "scripts/workflow_confirm_delete.html", {"wf": wf})
