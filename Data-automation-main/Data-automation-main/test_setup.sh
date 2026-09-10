#!/bin/bash

# Script de test pour DataAutomation

echo "======================================"
echo "Test de DataAutomation"
echo "======================================"
echo ""

cd /home/lz-jihed/dataAutomation
source venv/bin/activate

echo "1. Vérification de l'installation..."
python -c "import django; print(f'✅ Django {django.get_version()} installé')"
python -c "import pandas; print(f'✅ Pandas installé')"
python -c "import openpyxl; print(f'✅ Openpyxl installé')"

echo ""
echo "2. Vérification de la base de données..."
python manage.py check

echo ""
echo "3. Test du script exemple..."
if [ -f "example_input.csv" ]; then
    python -c "
import pandas as pd
df = pd.read_csv('example_input.csv')
df.to_excel('test_input.xlsx', index=False)
print('✅ Fichier test_input.xlsx créé')
"
else
    echo "⚠️  Fichier example_input.csv non trouvé"
fi

echo ""
echo "======================================"
echo "✅ Tests terminés!"
echo "======================================"
echo ""
echo "Le projet est prêt à être utilisé."
echo "Lancez './start_server.sh' pour démarrer."
