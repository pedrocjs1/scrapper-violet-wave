import gspread
import pandas as pd
import re
from app.core.config import settings

class GSheetService:
    def __init__(self, spreadsheet_id=None):
        """
        Si recibe spreadsheet_id, abre esa hoja específica.
        Si no, abre la hoja por defecto del archivo de configuración.
        """
        self.client = gspread.service_account(filename=settings.GOOGLE_CREDENTIALS_FILE)
        
        if spreadsheet_id:
            # Abre por ID (el código largo de la URL)
            try:
                self.sheet = self.client.open_by_key(spreadsheet_id).sheet1
            except Exception as e:
                print(f"[ERROR] No pude abrir la hoja con ID {spreadsheet_id}. Error: {e}")
                # Fallback: Si falla, intentamos abrir la default para no romper todo, o lanzamos error.
                raise e
        else:
            # Comportamiento por defecto (tu hoja maestra)
            self.sheet = self.client.open(settings.GOOGLE_SHEET_NAME).sheet1

    def load_new_leads(self) -> pd.DataFrame:
        all_records = self.sheet.get_all_records()
        df = pd.DataFrame(all_records)
        if df.empty or 'Status' not in df.columns:
            return pd.DataFrame()
        return df[df['Status'] == 'New']

    def update_lead_status(self, row_index: int, new_status: str):
        actual_row = row_index + 2
        headers = self.sheet.row_values(1)
        status_col = headers.index('Status') + 1
        self.sheet.update_cell(actual_row, status_col, new_status)

    def _normalize_phone(self, phone):
        """Deja solo los números."""
        return re.sub(r'\D', '', str(phone))

    def add_leads(self, leads_list: list) -> int:
        """
        Agrega leads validando que el teléfono no exista ya en el Excel.
        Retorna la cantidad de leads agregados.
        """
        try:
            # 1. Obtener todos los teléfonos actuales del Excel para comparar
            all_records = self.sheet.get_all_records()
            existing_df = pd.DataFrame(all_records)
            
            existing_phones = set()
            if not existing_df.empty and 'Phone' in existing_df.columns:
                # Normalizamos los teléfonos existentes para comparar bien
                existing_phones = set(self._normalize_phone(p) for p in existing_df['Phone'].astype(str))

            rows_to_add = []
            count_new = 0

            for lead in leads_list:
                raw_phone = lead.get('Phone', '')
                clean_phone = self._normalize_phone(raw_phone)
                
                # LA REGLA DE ORO: Si el teléfono ya existe, LO SALTAMOS.
                if clean_phone in existing_phones:
                    continue
                
                # Si es nuevo, lo preparamos
                row = [
                    lead.get('Nombre', ''),
                    raw_phone,   # Guardamos el original con formato
                    "New", 
                    lead.get('Notas', '') 
                ]
                rows_to_add.append(row)
                existing_phones.add(clean_phone) # Lo agregamos al set temporal para no duplicar en la misma carga
                count_new += 1

            # 2. Guardar en bloque
            if rows_to_add:
                self.sheet.append_rows(rows_to_add)
                print(f"[OK] Se agregaron {count_new} leads NUEVOS.")
            else:
                print("[AVISO] Todos los leads encontrados ya existian en el Excel.")
            
            return count_new
                
        except Exception as e:
            print(f"[ERROR] Guardando en Excel: {e}")
            return 0

    def update_status_by_phone(self, target_phone: str, new_status: str):
        """Busca el teléfono limpiando símbolos para asegurar coincidencia."""
        try:
            # 1. Limpiamos el teléfono que buscamos
            target_clean = self._normalize_phone(target_phone)
            
            # 2. Traemos toda la columna de teléfonos
            headers = self.sheet.row_values(1)
            try:
                # Buscamos 'Phone' o 'phone'
                if 'Phone' in headers:
                    phone_col_index = headers.index('Phone') + 1
                elif 'phone' in headers:
                    phone_col_index = headers.index('phone') + 1
                else:
                    # Si no encuentra, asume columna 2 (B)
                    phone_col_index = 2
                
                status_col_index = headers.index('Status') + 1
            except ValueError:
                print("[ERROR] No encuentro columna Status en el Excel")
                return False

            phone_column_values = self.sheet.col_values(phone_col_index)

            # 3. Iteramos para encontrar coincidencia
            found_row = -1
            
            for i, val in enumerate(phone_column_values):
                val_clean = self._normalize_phone(val)
                # Comparamos los últimos 8 dígitos
                if val_clean and target_clean.endswith(val_clean[-8:]): 
                    found_row = i + 1
                    break
            
            if found_row > 1:
                self.sheet.update_cell(found_row, status_col_index, new_status)
                print(f"[OK] Excel actualizado en fila {found_row}: {new_status}")
                return True
            else:
                print(f"[WARN] Telefono {target_phone} no encontrado en Excel.")
                return False

        except Exception as e:
            print(f"[ERROR CRITICO] en Excel: {e}")
            return False