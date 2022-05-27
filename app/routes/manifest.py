from flask import Blueprint, request

from . import MANIFEST
from .utils import respond_with

manifest_blueprint = Blueprint('manifest', __name__)


@manifest_blueprint.route('/<token>/manifest.json')
def addon_manifest(token: str):
    return respond_with(MANIFEST)
