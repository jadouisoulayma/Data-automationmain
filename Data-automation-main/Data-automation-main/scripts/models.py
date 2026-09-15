from django.db import models
from django.contrib.auth.models import User
import os


class Script(models.Model):
    """Model for storing Python scripts created by users"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    code = models.TextField()
    default_variables = models.JSONField(blank=True, null=True, default=dict)  # Default variable names
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scripts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"


class AdminFile(models.Model):
    """Model for storing admin files (models, env, configs, etc.)"""
    FILE_TYPE_CHOICES = [
        ('model', 'Modèle de données'),
        ('env', 'Fichier environnement'),
        ('config', 'Configuration'),
        ('template', 'Template'),
        ('other', 'Autre'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    file = models.FileField(upload_to='admin_files/', verbose_name='Fichier')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, verbose_name='Type')
    file_size = models.BigIntegerField(default=0, verbose_name='Taille (octets)')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Importé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Fichier Admin'
        verbose_name_plural = 'Fichiers Admin'
    
    def __str__(self):
        return f"{self.name} ({self.get_file_type_display()})"
    
    def get_filename(self):
        """Get the basename of the file"""
        if self.file:
            return os.path.basename(self.file.name)
        return ""
    
    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['octets', 'Ko', 'Mo', 'Go']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} To"
    
    def save(self, *args, **kwargs):
        """Save file size on upload"""
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Delete file from storage when model is deleted"""
        if self.file:
            try:
                if os.path.isfile(self.file.path):
                    os.remove(self.file.path)
            except Exception:
                pass
        super().delete(*args, **kwargs)


class ProductWorkflow(models.Model):
    """Workflow de traitement produits — pipeline complet depuis le notebook."""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('running', 'En cours'),
        ('success', 'Terminé'),
        ('error', 'Erreur'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_workflows')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)          # 0-100
    progress_message = models.CharField(max_length=300, blank=True)

    # Fichiers d'entrée (uploadés par l'utilisateur ou issus du dossier script data)
    input_file = models.FileField(upload_to='workflow/inputs/', blank=True, null=True,
                                  verbose_name='Fichier stock (input.xlsx)')
    backoffice_file = models.FileField(upload_to='workflow/backoffice/', blank=True, null=True,
                                       verbose_name='Données backoffice (.csv)')
    training_file = models.FileField(upload_to='workflow/training/', blank=True, null=True,
                                     verbose_name="Dataset d'entraînement (.csv)")

    # Fichier résultat (stockés dans workflow/resultats/ uniquement)
    output_file = models.FileField(upload_to='workflow/resultats/', blank=True, null=True,
                                   verbose_name='Fichier Excel résultat (produits finaux)')
    output_erreurs_file = models.FileField(upload_to='workflow/resultats/', blank=True, null=True,
                                           verbose_name='Fichier Excel lignes avec erreurs')
    output_dupliques_file = models.FileField(upload_to='workflow/resultats/', blank=True, null=True,
                                             verbose_name='Fichier Excel produits dupliqués')
    output_non_dupliques_file = models.FileField(upload_to='workflow/resultats/', blank=True, null=True,
                                                 verbose_name='Fichier Excel produits non dupliqués')

    logs = models.TextField(blank=True)
    nb_lignes_input = models.IntegerField(default=0)
    nb_lignes_output = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Workflow Produits'
        verbose_name_plural = 'Workflows Produits'

    def __str__(self):
        return f"Workflow #{self.pk} — {self.user.username} — {self.get_status_display()}"

    def get_input_filename(self):
        if self.input_file:
            return os.path.basename(self.input_file.name)
        return "input.xlsx (défaut)"

    def get_output_filename(self):
        if self.output_file:
            return os.path.basename(self.output_file.name)
        return ""

    def delete(self, *args, **kwargs):
        for f in (self.input_file, self.backoffice_file, self.training_file,
                  self.output_file, self.output_erreurs_file,
                  self.output_dupliques_file, self.output_non_dupliques_file):
            if f:
                try:
                    if os.path.isfile(f.path):
                        os.remove(f.path)
                except Exception:
                    pass
        super().delete(*args, **kwargs)


class ScriptExecution(models.Model):
    """Model for storing script execution history"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('error', 'Error'),
    ]

    script = models.ForeignKey(Script, on_delete=models.CASCADE, related_name='executions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    logs = models.TextField(blank=True)
    input_file = models.FileField(upload_to='inputs/', blank=True, null=True)
    output_file = models.FileField(upload_to='outputs/', blank=True, null=True)
    variables = models.JSONField(blank=True, null=True, default=dict)  # Store custom variables
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-executed_at']

    def __str__(self):
        return f"{self.script.name} - {self.user.username} - {self.status}"

    def get_input_filename(self):
        """Get the basename of the input file"""
        if self.input_file:
            return os.path.basename(self.input_file.name)
        return ""

    def get_output_filename(self):
        """Get the basename of the output file"""
        if self.output_file:
            return os.path.basename(self.output_file.name)
        return ""

    def save(self, *args, **kwargs):
        """Override save to implement storage cleanup (keep all executions but limit files)"""
        super().save(*args, **kwargs)
        
        # Keep all execution records (logs) but clean up old files to save storage
        # Delete files from executions older than the last 5 per script
        executions_per_script = ScriptExecution.objects.filter(script=self.script).order_by('-executed_at')
        if executions_per_script.count() > 5:
            old_executions = executions_per_script[5:]
            for exec in old_executions:
                # Only delete files, keep the execution record and logs
                self._delete_files_only(exec)
        
        # Global limit: Delete files from executions older than the last 100 total
        all_executions = ScriptExecution.objects.all().order_by('-executed_at')
        if all_executions.count() > 100:
            old_executions = all_executions[100:]
            for exec in old_executions:
                # Only delete files, keep the execution record and logs
                self._delete_files_only(exec)
    
    @staticmethod
    def _delete_files_only(execution):
        """Delete only files, keep execution record and logs"""
        if execution.input_file:
            try:
                if os.path.isfile(execution.input_file.path):
                    os.remove(execution.input_file.path)
                execution.input_file = None
            except Exception:
                pass
        if execution.output_file:
            try:
                if os.path.isfile(execution.output_file.path):
                    os.remove(execution.output_file.path)
                execution.output_file = None
            except Exception:
                pass
        # Save without triggering save() again to avoid recursion
        ScriptExecution.objects.filter(pk=execution.pk).update(
            input_file=None,
            output_file=None
        )
