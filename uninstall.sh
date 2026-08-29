#!/usr/bin/env bash
# ============================================================================
#  DÉSINSTALLATION de l'environnement de simulation.
#
#  NE TOUCHE PAS : ton code ni logs/ (points de contrôle et journaux).
#
#      ./uninstall.sh              # ce qui n'appartient qu'à ce dépôt
#      ./uninstall.sh --partage    # + LE CONTENEUR et le venv commun
#      ./uninstall.sh --image      # + l'image de base (~15-20 Go)
#      ./uninstall.sh --tout       # TOUT : conteneur, venv, image
#      ./uninstall.sh --tout -y    # idem, sans confirmation
#
#  ---------------------------------------------------------------------------
#  POURQUOI LE PARTAGÉ DEMANDE UN DRAPEAU
#
#  Le conteneur et le venv portent des noms GÉNÉRIQUES : d'autres projets
#  installés de la même façon s'en servent aussi. Les supprimer derrière une
#  seule question « Continuer ? » casserait silencieusement l'environnement
#  des autres.
#
#  Une suppression n'énumère jamais « tout ce que je crois t'appartenir ».
#  Elle énumère ce qu'on sait remplacer sans coût pour personne d'autre ; le
#  reste demande un geste explicite.
# ============================================================================
set -e

PARTAGE=0
IMAGE_AUSSI=0
OUI=0
for arg in "$@"; do
    case "$arg" in
        --partage|--shared) PARTAGE=1 ;;
        --image)            IMAGE_AUSSI=1 ;;
        --tout|--all)       PARTAGE=1; IMAGE_AUSSI=1 ;;
        -y|--yes)           OUI=1 ;;
        -h|--help)          sed -n '2,23p' "$0"; exit 0 ;;
        *) echo "Argument inconnu : $arg" >&2; exit 1 ;;
    esac
done

BOX="${BOX_NAME:-genesis-box}"
IMAGE="${BOX_IMAGE:-docker.io/rocm/pytorch:rocm7.2.4_ubuntu24.04_py3.12_pytorch_release_2.10.0}"
VENV="${VENV_DIR:-$HOME/venvs/genesis}"
PROJET="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Liste UNIQUE : ce qui est annoncé est exactement ce qui sera effacé. Deux
# listes séparées finissent toujours par diverger, et un script de suppression
# qui efface plus que ce qu'il annonce n'est pas digne de confiance.
# Balayage plutôt qu'une liste figée : on ramasse TOUS les `__pycache__` du
# dépôt, y compris ceux de dossiers qui n'existaient pas quand ce script a été
# écrit. Une liste en dur se périme et laisse des restes.
mapfile -t A_SUPPRIMER < <(
    find "$PROJET" -type d -name "__pycache__" -not -path "*/.git/*" 2>/dev/null
    [ -d "$PROJET/.venv" ] && echo "$PROJET/.venv"
)

echo "Va être supprimé :"
LOCAL_TROUVE=0
for d in "${A_SUPPRIMER[@]}"; do
    [ -e "$d" ] && { echo "  - $d"; LOCAL_TROUVE=1; }
done
[ "$LOCAL_TROUVE" -eq 0 ] && echo "  - (rien qui n'appartienne à ce seul dépôt)"
if [ "$PARTAGE" -eq 1 ]; then
    echo "  - le venv commun     : $VENV"
    echo "  - le conteneur       : $BOX"
    echo
    echo "  ⚠️  Ces deux-là sont PARTAGÉS. Tout autre projet qui s'en sert"
    echo "      cessera de fonctionner jusqu'à sa réinstallation."
fi
[ "$IMAGE_AUSSI" -eq 1 ] && echo "  - l'image de base    : ~15-20 Go à retélécharger"
echo "  (le code et logs/ sont conservés)"

if [ "$PARTAGE" -eq 0 ]; then
    echo
    echo "⚠️  LE CONTENEUR '$BOX' N'EST PAS SUPPRIMÉ par cet appel."
    echo "    Pour l'enlever avec le venv commun :   ./uninstall.sh --partage"
    echo "    Pour tout enlever (+ l'image) :        ./uninstall.sh --tout"
fi

if [ "$OUI" -eq 0 ]; then
    read -r -p $'\nContinuer ? [o/N] ' rep
    [[ "$rep" =~ ^[oOyY] ]] || { echo "Annulé."; exit 0; }
fi

rm -rf "${A_SUPPRIMER[@]}" 2>/dev/null || true
echo "Fichiers propres au dépôt supprimés."

if [ "$PARTAGE" -eq 1 ]; then
    if [ -d "$VENV" ]; then rm -rf "$VENV"; echo "venv commun supprimé."
    else echo "venv commun déjà absent."; fi
    # Comparaison EXACTE (grep -qx) et via le moteur, pas via le tableau de
    # `distrobox list` : en sous-chaîne, « genesis-box » désignerait aussi
    # « genesis-box-cuda », et on supprimerait le conteneur d'à côté.
    MOTEUR="$(command -v podman || command -v docker || true)"
    if [ -n "$MOTEUR" ] && "$MOTEUR" ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$BOX"; then
        distrobox rm --force "$BOX"; echo "conteneur supprimé."
    else echo "conteneur déjà absent."; fi
fi

if [ "$IMAGE_AUSSI" -eq 1 ]; then
    # `rmi` échoue tant qu'un conteneur s'en sert : c'est exactement la garde
    # qu'on veut, et on ne la force jamais.
    (podman rmi "$IMAGE" 2>/dev/null || docker rmi "$IMAGE" 2>/dev/null) \
        && echo "image supprimée." \
        || echo "image introuvable ou encore utilisée — conservée."
fi

echo "Désinstallation terminée."
