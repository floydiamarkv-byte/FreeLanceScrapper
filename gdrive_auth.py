#!/usr/bin/env python3
"""
Google Drive API — Autenticación OAuth2
Ejecutar UNA VEZ para generar token.json
Después el token se reutiliza automáticamente.
"""
import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes — acceso completo a Drive
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]

BASE_DIR = Path(__file__).parent
CREDS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def authenticate():
    """Autentica con Google OAuth2 y devuelve las credenciales."""
    creds = None

    # Si ya existe un token, lo reutiliza
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Si no hay credenciales válidas, hacer login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refrescando token expirado...")
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                raise FileNotFoundError(
                    f"❌ No se encontró {CREDS_FILE}\n"
                    "Descárgalo desde Google Cloud Console → APIs → Credentials"
                )
            print("🔐 Iniciando autenticación OAuth2...")
            print("   Se abrirá tu navegador para autorizar acceso.\n")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Guardar token para futuros usos
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print(f"💾 Token guardado en: {TOKEN_FILE}")

    return creds


def get_drive_service():
    """Devuelve un servicio autenticado de Google Drive."""
    creds = authenticate()
    return build("drive", "v3", credentials=creds)


def get_or_create_drive_folder(service, folder_name: str, parent_id: str = None) -> str:
    """
    Busca una carpeta por nombre en Drive. Si no existe, la crea.
    Devuelve el ID de la carpeta.
    """
    # Buscar carpeta existente
    query = (
        f"name = '{folder_name}' and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"trashed = false"
    )
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(
        q=query, spaces="drive", fields="files(id, name)", pageSize=1
    ).execute()

    files = results.get("files", [])
    if files:
        print(f"  📁 Carpeta encontrada: {folder_name} (ID: {files[0]['id']})")
        return files[0]["id"]

    # Crear carpeta si no existe
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    print(f"  📁 Carpeta creada: {folder_name} (ID: {folder['id']})")
    return folder["id"]


def get_docs_service():
    """Devuelve un servicio autenticado de Google Docs."""
    creds = authenticate()
    return build("docs", "v1", credentials=creds)


def get_sheets_service():
    """Devuelve un servicio autenticado de Google Sheets."""
    creds = authenticate()
    return build("sheets", "v4", credentials=creds)


if __name__ == "__main__":
    print("=" * 50)
    print("🔑 Google Drive API — Autenticación")
    print("=" * 50)

    creds = authenticate()
    service = build("drive", "v3", credentials=creds)

    # Prueba: listar los 10 archivos más recientes
    print("\n✅ ¡Autenticación exitosa!")
    print("\n📁 Tus 10 archivos más recientes en Google Drive:\n")

    results = service.files().list(
        pageSize=10,
        fields="files(id, name, mimeType, modifiedTime)",
        orderBy="modifiedTime desc",
    ).execute()

    files = results.get("files", [])
    if not files:
        print("   (No se encontraron archivos)")
    else:
        for f in files:
            icon = "📄"
            if "folder" in f.get("mimeType", ""):
                icon = "📁"
            elif "spreadsheet" in f.get("mimeType", ""):
                icon = "📊"
            elif "document" in f.get("mimeType", ""):
                icon = "📝"
            elif "presentation" in f.get("mimeType", ""):
                icon = "📽️"
            print(f"   {icon} {f['name']}")
            print(f"      ID: {f['id']}")
            print(f"      Modificado: {f['modifiedTime'][:10]}")
            print()

    print("🎉 ¡Google Drive conectado correctamente!")
