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
    workflows = ProductWorkflow.objects.filter(user=request.user)[:3]

    # Vérification disponibilité des fichiers par défaut
    defaults = {
        "input_ok": os.path.isfile(DEFAULT_INPUT),
        "backoffice_ok": os.path.isfile(DEFAULT_BACKOFFICE),
        "training_ok": os.path.isfile(DEFAULT_TRAINING),
    }

    # Les 10 étapes sont codées directement dans le template pour plus de clarté
    return render(request, "scripts/workflow_produits.html", {
        "workflows": workflows,
        "defaults":  defaults,
    })


@login_required
def workflow_produits_run(request):
    """Lance un nouveau workflow produits (POST)."""
    if request.method != "POST":
        return redirect("workflow_produits")

    # ── Validation : input obligatoire, backoffice optionnel (réutilise le dernier si absent) ──
    has_input      = "input_file"      in request.FILES and bool(request.FILES["input_file"])
    has_backoffice = "backoffice_file" in request.FILES and bool(request.FILES["backoffice_file"])
    has_training   = os.path.isfile(DEFAULT_TRAINING)   # fichier fixe backend, toujours vérifié

    manquants_pre = []
    if not has_input:      manquants_pre.append("le fichier de stock (input.xlsx)")
    if not has_training:   manquants_pre.append("le modèle IA (contacter l'administrateur)")

    if manquants_pre:
        messages.error(
            request,
            "Veuillez ajouter les fichiers demandés avant de lancer le pipeline : "
            + ", ".join(manquants_pre) + "."
        )
        return redirect("workflow_produits")

    # Créer l'entrée en base seulement si tout est disponible
    wf = ProductWorkflow.objects.create(user=request.user, status="pending", progress=0)

    # Gérer les fichiers : upload utilisateur OU récupération automatique du dernier
    import datetime as _dt
    import glob

    def _sauvegarder_ou_defaut(field_name, default_path, wf_field_attr):
        """
        Upload le fichier utilisateur OU récupère le dernier fichier du dossier.
        - Si l'utilisateur a uploadé → on sauvegarde avec timestamp
        - Sinon → on récupère le dernier fichier par date (pour backoffice)
        """
        if field_name in request.FILES:
            f = request.FILES[field_name]
            # Nommage datetime : YYYY-MM-DD_HH.MM.SS + extension originale
            ext      = os.path.splitext(f.name)[1].lower()
            nom_date = _dt.datetime.now().strftime("%Y-%m-%d_%H.%M.%S") + ext
            getattr(wf, wf_field_attr).save(nom_date, f, save=False)
            return None  # fichier uploadé, pas besoin de chemin externe

        # ── Récupération automatique du dernier fichier (pour backoffice) ──
        if field_name == "backoffice_file":
            from django.conf import settings
            backoffice_dir = os.path.join(settings.MEDIA_ROOT, "workflow", "backoffice")
            if os.path.isdir(backoffice_dir):
                # Chercher tous les fichiers .csv dans le dossier
                csv_files = sorted(
                    glob.glob(os.path.join(backoffice_dir, "*.csv")),
                    key=os.path.getmtime,  # tri par date de modification
                    reverse=True           # du plus récent au plus ancien
                )
                if csv_files:
                    dernier_backoffice = csv_files[0]
                    logger.info(f"Fichier backoffice non uploadé → réutilisation automatique : {dernier_backoffice}")
                    return dernier_backoffice

        return default_path  # fallback sur le fichier par défaut si configuré

    chemin_input      = _sauvegarder_ou_defaut("input_file",     DEFAULT_INPUT,      "input_file")
    chemin_backoffice = _sauvegarder_ou_defaut("backoffice_file", DEFAULT_BACKOFFICE, "backoffice_file")
    chemin_training   = DEFAULT_TRAINING   # toujours le fichier fixe — pas d'upload
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
    path_training   = DEFAULT_TRAINING   # fichier fixe backend

    # Validation secondaire
    manquants = []
    if not path_input:                        manquants.append("input.xlsx")
    if not path_backoffice:                   manquants.append("databackoffice.csv")
    if not os.path.isfile(path_training):     manquants.append("entarinementdataset.csv")

    if manquants:
        wf.status = "error"
        wf.logs = f"Fichiers manquants : {', '.join(manquants)}"
        wf.save()
        messages.error(request, f"Fichiers manquants : {', '.join(manquants)}")
        return redirect("workflow_produits")

    # Dossier de sortie — le pipeline crée lui-même le sous-dossier daté YYYYMMDD_HHMMSS
    # et applique la rotation FIFO (3 derniers résultats conservés)
    from django.conf import settings
    output_dir = os.path.join(settings.MEDIA_ROOT, "workflow", "resultats")

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

            # Lire le rapport JSON généré par le pipeline
            import json
            run_dir     = os.path.dirname(output_path)
            ts_run      = os.path.basename(run_dir)
            rapport_path = os.path.join(run_dir, f"{ts_run}_rapport.json")
            rapport_info = ""
            if os.path.isfile(rapport_path):
                with open(rapport_path, "r", encoding="utf-8") as fj:
                    rapport = json.load(fj)
                # date_execution est déjà au format lisible YYYY-MM-DD HH:MM:SS
                rapport_info = (
                    f"\n📊 Rapport [{rapport.get('date_execution', '')}] : "
                    f"{rapport.get('nb_produits_traites', '?')} produits "
                    f"| {rapport.get('nb_lignes_erreurs', '?')} erreurs "
                    f"| {rapport.get('nb_dupliques', '?')} dupliqués"
                    f"\n📁 Dossier résultat : {run_dir}"
                )

            # Lire le résultat pour compter les lignes
            import pandas as pd
            df_out = pd.read_excel(output_path)
            nb_out = len(df_out)

            # ── Assigner les chemins relatifs (depuis MEDIA_ROOT) sans copier ─────
            from django.conf import settings
            MEDIA_ROOT = settings.MEDIA_ROOT

            def rel_media(absolute_path):
                """Retourne le chemin relatif depuis MEDIA_ROOT."""
                return os.path.relpath(absolute_path, MEDIA_ROOT)

            wf_db = ProductWorkflow.objects.get(pk=wf.pk)
            wf_db.output_file = rel_media(output_path)

            # Assigner les fichiers secondaires (erreurs, dupliqués, non-dupliqués)
            if output_erreurs_path and os.path.isfile(output_erreurs_path):
                wf_db.output_erreurs_file = rel_media(output_erreurs_path)
            if output_dupliques_path and os.path.isfile(output_dupliques_path):
                wf_db.output_dupliques_file = rel_media(output_dupliques_path)
            if output_non_dup_path and os.path.isfile(output_non_dup_path):
                wf_db.output_non_dupliques_file = rel_media(output_non_dup_path)

            wf_db.status = "success"
            wf_db.progress = 100
            wf_db.nb_lignes_output = nb_out
            wf_db.finished_at = timezone.now()
            wf_db.logs = "\n".join(logs_lines) + f"\n[100%] ✅ {nb_out} produits exportés." + rapport_info
            wf_db.save()

            # ── Suppression des fichiers input/backoffice pour libérer l'espace ──
            try:
                if wf_db.input_file and wf_db.input_file.name:
                    input_path = wf_db.input_file.path
                    if os.path.isfile(input_path):
                        os.remove(input_path)
                        logger.info(f"Fichier input supprimé : {input_path}")
                    wf_db.input_file = None

                if wf_db.backoffice_file and wf_db.backoffice_file.name:
                    backoffice_path = wf_db.backoffice_file.path
                    if os.path.isfile(backoffice_path):
                        os.remove(backoffice_path)
                        logger.info(f"Fichier backoffice supprimé : {backoffice_path}")
                    wf_db.backoffice_file = None

                wf_db.save(update_fields=["input_file", "backoffice_file"])
            except Exception as e:
                logger.warning(f"Impossible de supprimer les fichiers uploadés : {e}")

            # ── FIFO : rotation automatique après chaque run réussi ───────
            from .fifo import appliquer_fifo
            appliquer_fifo()

        except Exception as exc:
            err = traceback.format_exc()
            logger.error("Workflow #%s erreur : %s", wf.pk, err)
            ProductWorkflow.objects.filter(pk=wf.pk).update(
                status="error",
                logs="\n".join(logs_lines) + f"\n❌ ERREUR :\n{err}",
                finished_at=timezone.now(),
            )

            # ── Suppression des fichiers input/backoffice même en cas d'erreur ──
            try:
                wf_db = ProductWorkflow.objects.get(pk=wf.pk)
                if wf_db.input_file and wf_db.input_file.name:
                    input_path = wf_db.input_file.path
                    if os.path.isfile(input_path):
                        os.remove(input_path)
                        logger.info(f"Fichier input supprimé (après erreur) : {input_path}")
                    wf_db.input_file = None

                if wf_db.backoffice_file and wf_db.backoffice_file.name:
                    backoffice_path = wf_db.backoffice_file.path
                    if os.path.isfile(backoffice_path):
                        os.remove(backoffice_path)
                        logger.info(f"Fichier backoffice supprimé (après erreur) : {backoffice_path}")
                    wf_db.backoffice_file = None

                wf_db.save(update_fields=["input_file", "backoffice_file"])
            except Exception as e:
                logger.warning(f"Impossible de supprimer les fichiers uploadés après erreur : {e}")

            # ── FIFO : rotation aussi en cas d'erreur ─────────────────────
            try:
                from .fifo import appliquer_fifo
                appliquer_fifo()
            except Exception:
                pass

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

    # ── Extraction et traduction du message d'erreur ──────────────────────
    error_message = None
    error_etape   = None
    if wf.status == "error" and wf.logs:
        logs = wf.logs

        # Dictionnaire : mot-clé dans les logs → message clair pour l'utilisateur
        ERREURS_CONNUES = [
            ("Colonne obligatoire introuvable",
             "Le fichier de stock ne contient pas toutes les colonnes requises.",
             "Vérifiez que votre fichier contient bien les colonnes : nom du produit, EAN, état, pc, prix de vente, quantité."),
            ("Impossible de lire",
             "Le fichier envoyé ne peut pas être lu.",
             "Assurez-vous que le fichier n'est pas corrompu et qu'il est bien au format .xlsx ou .csv."),
            ("Colonnes backoffice introuvables",
             "Le fichier catalogue (backoffice) n'a pas le bon format.",
             "Vérifiez que votre fichier backoffice contient les colonnes 'name' et 'ean13'."),
            ("Colonnes ML introuvables",
             "Le fichier d'entraînement IA n'a pas le bon format.",
             "Contactez l'administrateur — le fichier d'entraînement doit contenir : name, id_marque, id_category."),
            ("FileNotFoundError",
             "Un fichier requis est introuvable sur le serveur.",
             "Réessayez en déposant à nouveau vos fichiers. Si le problème persiste, contactez l'administrateur."),
            ("PermissionError",
             "Le serveur n'a pas les droits pour accéder à un fichier.",
             "Contactez l'administrateur système."),
            ("MemoryError",
             "Le fichier est trop volumineux pour être traité.",
             "Réduisez la taille de votre fichier et relancez le traitement."),
            ("UnicodeDecodeError",
             "Le fichier contient des caractères non reconnus.",
             "Sauvegardez votre fichier CSV en encodage UTF-8 et réessayez."),
            ("openpyxl",
             "Le fichier Excel est invalide ou endommagé.",
             "Ouvrez votre fichier dans Excel, sauvegardez-le à nouveau, puis réessayez."),
            ("ERREUR",
             "Une erreur s'est produite pendant le traitement.",
             "Consultez le détail ci-dessous ou contactez l'administrateur."),
        ]

        for mot_cle, titre, conseil in ERREURS_CONNUES:
            if mot_cle.lower() in logs.lower():
                error_message = titre
                error_etape   = conseil
                break

        if not error_message:
            error_message = "Une erreur inattendue s'est produite pendant le traitement."
            error_etape   = "Consultez le détail technique dans les logs ou contactez l'administrateur."

        # Extraire l'étape où l'erreur s'est produite (ex: "Etape 2")
        import re
        m = re.search(r'Etape\s*\d+\w*', logs, re.IGNORECASE)
        if m:
            error_etape = f"Erreur détectée à l'étape : {m.group(0)}. " + (error_etape or "")

    return JsonResponse({
        "status":   wf.status,
        "progress": wf.progress,
        "message":  wf.progress_message,
        "logs":     wf.logs,
        "nb_lignes_output": wf.nb_lignes_output,
        "error_message":    error_message,
        "error_etape":      error_etape,
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


@login_required
def workflow_produits_reporting(request, pk):
    """
    Page de reporting détaillé d'un workflow :
    - Temps d'exécution total et par phase
    - Stats globales (produits traités, erreurs, dupliqués, non-dupliqués)
    - Répartition des types d'erreurs de saisie (vide, négatif, = 0, non numérique)
    - Liste complète des lignes avec erreurs de saisie
    """
    import json as _json
    import pandas as _pd
    import datetime as _dt

    wf = get_object_or_404(ProductWorkflow, pk=pk, user=request.user)
    if wf.status != "success":
        messages.error(request, "Le reporting n'est disponible que pour les pipelines terminés avec succès.")
        return redirect("workflow_produits")

    # ── Temps d'exécution ─────────────────────────────────────────────────
    duree_secondes = None
    duree_fmt      = "—"
    if wf.created_at and wf.finished_at:
        delta = wf.finished_at - wf.created_at
        duree_secondes = int(delta.total_seconds())
        m, s = divmod(duree_secondes, 60)
        duree_fmt = f"{m}m {s:02d}s" if m else f"{s}s"

    # ── Rapport JSON ───────────────────────────────────────────────────────
    rapport = {}
    if wf.output_file and wf.output_file.name:
        run_dir      = os.path.dirname(wf.output_file.path)
        ts_run       = os.path.basename(run_dir)
        rapport_path = os.path.join(run_dir, f"{ts_run}_rapport.json")
        if os.path.isfile(rapport_path):
            with open(rapport_path, "r", encoding="utf-8") as fj:
                rapport = _json.load(fj)

    # ── Analyse des lignes avec erreurs de saisie ─────────────────────────
    erreurs_rows  = []
    types_erreurs = {}   # { "pc vide": 3, "quantite = 0": 1, ... }

    # Catégories d'erreurs de saisie pour le dashboard
    cat_erreurs = {
        "vide":         {"label": "Champ vide",      "color": "#dc2626", "count": 0},
        "zero":         {"label": "Valeur = 0",       "color": "#d97706", "count": 0},
        "negatif":      {"label": "Valeur négative",  "color": "#7c3aed", "count": 0},
        "non_numerique":{"label": "Non numérique",    "color": "#0891b2", "count": 0},
    }

    if wf.output_erreurs_file and wf.output_erreurs_file.name:
        try:
            df_err = _pd.read_excel(wf.output_erreurs_file.path)
            col_err = next((c for c in df_err.columns
                            if c.strip().lower() in ("erreur", "error", "raison_erreur")), None)
            if col_err and col_err != "Erreur":
                df_err = df_err.rename(columns={col_err: "Erreur"})

            if "Erreur" in df_err.columns:
                for _, row in df_err.iterrows():
                    row_dict = {
                        k.replace(" ", "_"): (None if (not isinstance(v, str) and _pd.isna(v)) else v)
                        for k, v in row.items()
                    }
                    erreurs_rows.append(row_dict)

                    # Comptage par type et par catégorie
                    causes = [e.strip() for e in str(row.get("Erreur", "")).split(";")
                              if e.strip() and e.strip() not in ("nan", "None")]
                    for cause in causes:
                        types_erreurs[cause] = types_erreurs.get(cause, 0) + 1
                        cl = cause.lower()
                        if "vide" in cl:
                            cat_erreurs["vide"]["count"] += 1
                        elif "= 0" in cl or "=0" in cl:
                            cat_erreurs["zero"]["count"] += 1
                        elif "negatif" in cl or "négatif" in cl:
                            cat_erreurs["negatif"]["count"] += 1
                        elif "non numerique" in cl or "non numérique" in cl:
                            cat_erreurs["non_numerique"]["count"] += 1
        except Exception as e:
            logger.warning("Reporting: impossible de lire fichier erreurs : %s", e)

    # ── Statistiques globales ─────────────────────────────────────────────
    nb_ok  = rapport.get("nb_produits_traites", 0)
    nb_err = len(erreurs_rows)
    nb_dup = rapport.get("nb_dupliques", 0)
    nb_non_dup = rapport.get("nb_non_dupliques", 0)
    nb_total = nb_ok + nb_err
    taux_erreur = round((nb_err / nb_total * 100), 1) if nb_total > 0 else 0

    # Vitesse de traitement (produits/seconde)
    vitesse = round(nb_total / duree_secondes, 1) if duree_secondes and duree_secondes > 0 else 0

    # Types triés par fréquence
    types_erreurs_sorted   = sorted(types_erreurs.items(), key=lambda x: x[1], reverse=True)
    cat_erreurs_list       = [(v["label"], v["color"], v["count"])
                               for v in cat_erreurs.values() if v["count"] > 0]
    total_cat              = sum(v["count"] for v in cat_erreurs.values())

    context = {
        "wf":                   wf,
        "rapport":              rapport,
        # Temps
        "duree_fmt":            duree_fmt,
        "duree_secondes":       duree_secondes,
        "vitesse":              vitesse,
        "date_debut":           wf.created_at,
        "date_fin":             wf.finished_at,
        # Volumes
        "nb_ok":                nb_ok,
        "nb_err":               nb_err,
        "nb_dup":               nb_dup,
        "nb_non_dup":           nb_non_dup,
        "nb_total":             nb_total,
        "taux_erreur":          taux_erreur,
        # Erreurs
        "erreurs_rows":         erreurs_rows,
        "types_erreurs":        types_erreurs_sorted,
        "total_types_erreurs":  sum(types_erreurs.values()),
        "cat_erreurs":          cat_erreurs_list,
        "total_cat":            total_cat,
    }
    return render(request, "scripts/workflow_reporting.html", context)
