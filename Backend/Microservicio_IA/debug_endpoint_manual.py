import os

import requests

url = 'http://localhost:5000/api/analyze'
img_dir = r'C:\Users\Miscar\Downloads\ecografias'
paths = ['eco_gemelos.jpg','gemelar.jpg','ecografia-bebe-semana-3ok.jpg','ecografia-y.ultrasonido.jpg','movimiento fetales.jpg','adenoma-14.png']

for path in paths:
    full = os.path.join(img_dir, path)
    if not os.path.exists(full):
        print('NOT FOUND:', path)
        continue
    with open(full, 'rb') as f:
        r = requests.post(url, files={'file': (path, f, 'image/jpeg')})
    data = r.json()
    dd = data.get('pathology_detection', {}).get('pathologies', [{}])[0]
    shap = data.get('shap_risk_scores', {})
    print(path)
    print('  ->', dd.get('pathology','?'), '({:.4f})'.format(dd.get('confidence',0)))
    if shap:
        pree = shap.get('riesgo_preeclampsia', 0)
        print('  -> riesgo_preeclampsia: {:.3f}'.format(pree))
        for k,v in shap.items():
            if k != 'riesgo_global':
                print('    {}: {:.3f}'.format(k, v))
    print()
