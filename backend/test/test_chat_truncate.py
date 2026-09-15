import sys
sys.path.insert(0, 'backend')
from app.api.v1.chat import _truncate_hallucination

cases = [
    (
        "Bonjour ! Pour réussir ton examen, révise tes intégrales.\n- Étudiant : D'accord et pour la physique ?\n- Assistant : Pour la physique...",
        "Bonjour ! Pour réussir ton examen, révise tes intégrales."
    ),
    (
        "Voici ton conseil d'étude.\n* Student: Thanks a lot!\n* Assistant: You are welcome!",
        "Voici ton conseil d'étude."
    ),
    (
        "Voici ta réponse.\n**Étudiant** : Super merci !\n**Assistant** : De rien.",
        "Voici ta réponse."
    ),
    (
        "Assistant : Bonne chance pour tes cours !\n\n[Étudiant] : Merci !",
        "Bonne chance pour tes cours !"
    ),
    (
        "Réponse : Voici les concepts clés.<|eot_id|>",
        "Voici les concepts clés."
    ),
    (
        "Pour le devoir, commence par l'exercice 2.\nQuestion de l'étudiant : Quel exercice ?",
        "Pour le devoir, commence par l'exercice 2."
    ),
    (
        "- Assistant : Planifie 2h de maths lundi.\n- Toi : D'accord !",
        "Planifie 2h de maths lundi."
    ),
    (
        "Voici ton planning optimisé.\n\n### HISTORIQUE\n- user: hello",
        "Voici ton planning optimisé."
    )
]

failed = 0
for i, (input_text, expected) in enumerate(cases):
    output = _truncate_hallucination(input_text)
    if output != expected:
        print(f"[FAIL] Case {i} failed:\n  Input:    {input_text!r}\n  Expected: {expected!r}\n  Got:      {output!r}")
        failed += 1
    else:
        print(f"[OK] Case {i} passed")

if failed == 0:
    print("\nALL TRUNCATION TESTS PASSED SUCCESSFULLY!")
else:
    sys.exit(1)
