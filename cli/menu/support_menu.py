# cli/menus/support_menu.py
from __future__ import annotations
"""
Menu CLI pour le rôle SUPPORT (version démo : actions commentées).

Fonctions prévues :
- Lister uniquement les événements assignés à l'utilisateur connecté.
- Mettre à jour un événement dont l'utilisateur est responsable.

⚠️ Pour activer une option :
   1) Décommente l’import correspondant.
   2) Décommente le code dans le bloc if/elif de l’option.
"""

# ⛔️ Imports volontairement commentés pour éviter l’exécution pendant la démo.
# from cli.services.events.get_events import list_events
# from cli.services.events.update_event import _input_int, _update_event_form_support
# from cli.utils.config import EVENT_URL
# from cli.utils.session import session


def support_menu() -> None:
    """
    Affiche le menu dédié au rôle SUPPORT et route les actions.
    - Option 1 : lister les événements dont `support_contact` = session.user.id
    - Option 2 : mettre à jour un événement assigné (horaires, notes, etc.)
    """
    while True:
        print("\n" + "=" * 50)
        print("🧭 MENU SUPPORT".center(50))
        print("=" * 50)
        print("1. Lister MES événements (assignés à moi)")
        print("2. Mettre à jour un de MES événements")
        print("0. Retour")

        choice = input("\nVotre choix : ").strip()

        # 1) Lister mes événements (filtre serveur : support_contact=<session.user.id>)
        if choice == "1":
            print("ℹ️ Action désactivée (listing de VOS événements assignés).")
            # if not session.user:
            #     print("❌ Utilisateur non connecté.")
            # else:
            #     list_events(
            #         params={"support_contact": session.user["id"]},
            #         display=True,
            #         as_table=True,
            #     )

        # 2) Mettre à jour un événement (si assigné au support connecté)
        elif choice == "2":
            print("ℹ️ Action désactivée (mise à jour d’un événement assigné).")
            # event_id = _input_int("ID de l’événement à modifier (ou 'retour') : ")
            # if event_id is None:
            #     continue
            # payload = _update_event_form_support(event_id)
            # if not payload:
            #     continue
            # resp = session.patch(f"{EVENT_URL}{event_id}/", json=payload)
            # if 200 <= resp.status_code < 300:
            #     print("✅ Événement mis à jour.")
            # else:
            #     print(f"❌ Erreur ({resp.status_code})")
            #     try:
            #         print("📨", resp.json())
            #     except ValueError:
            #         print("📨", resp.text)

        # Quitter le menu support
        elif choice == "0":
            return

        # Choix invalide
        else:
            print("❌ Choix invalide. Réessayez.")