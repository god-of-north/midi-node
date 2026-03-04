import json
import os
import shutil
from pathlib import Path
from typing import List, Optional

from .app_config import AppConfig
from .preset import Preset
from .bank import Bank

class StorageManager:
    def __init__(self, root_path: str, context: 'DeviceContext'):
        self.root = Path(root_path)
        self.preset_dir = self.root / "presets"
        self.bank_dir = self.root / "banks"
        self.config_dir = self.root / "config"
        self.context = context
        
        # Ensure directories exist
        self.preset_dir.mkdir(parents=True, exist_ok=True)
        self.bank_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    # --- Internal Utilities ---

    def _get_preset_path(self, number: int) -> Path:
        return self.preset_dir / f"{number:03d}.json"

    def _get_bank_path(self, number: int) -> Path:
        return self.bank_dir / f"{number:03d}.json"

    # --- Preset API ---

    def save_preset(self, number: int, preset: Preset):
        try:
            # firstly save data to temp file then move to avoid corruption
            temp_path = self._get_preset_path(number).with_suffix(".tmp")
            if temp_path.exists():
                os.remove(temp_path)
            with open(temp_path, 'w') as f:
                preset_dict = preset.to_dict()
                json.dump(preset_dict, f, indent=4)

            # Move temp file to final location, replace if exists
            final_path = self._get_preset_path(number)
            if final_path.exists():
                os.remove(final_path)
            temp_path.rename(final_path)
        except Exception as e:
            print(f"Error saving preset to file: {e}")


    def load_preset(self, number: int) -> Optional[Preset]:
        path = self._get_preset_path(number)
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return Preset.from_dict(json.load(f), context=self.context)

    def get_preset_list(self) -> List[dict]:
        """Returns list of {number: int, name: str}"""
        presets = []
        for file in sorted(self.preset_dir.glob("*.json")):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    presets.append({
                        "number": int(file.stem),
                        "name": data.get("name", "Unnamed")
                    })
            except Exception as e:
                print(f"Error loading preset file {file}: {e}")
                presets.append({
                    "number": int(file.stem),
                    "name": "Error"
                })
        return presets

    def reorder_presets(self, source_num: int, target_num: int, mode: str = "move"):
        """
        Handles moving/cloning and triggers bank updates.
        mode: 'move' (renames) or 'clone' (copies)
        """
        source_path = self._get_preset_path(source_num)
        target_path = self._get_preset_path(target_num)

        if not source_path.exists():
            raise FileNotFoundError(f"Source preset {source_num} not found.")

        # If target exists, we shift everything or overwrite? 
        # Expert choice: Let's implement a clean move and notify banks.
        if mode == "move":
            shutil.move(str(source_path), str(target_path))
            self._update_banks_on_preset_change(source_num, target_num)
        else:
            shutil.copy(str(source_path), str(target_path))

    def remove_preset(self, number: int):
        path = self._get_preset_path(number)
        if path.exists():
            os.remove(path)
            self._update_banks_on_preset_change(number, None) # None = Deleted

    def save_current_preset_index(self, preset_number: int):
        path = self.root / "current_preset.txt"
        with open(path, 'w') as f:
            f.write(str(preset_number))
    
    def load_current_preset_index(self) -> Optional[int]:
        path = self.root / "current_preset.txt"
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return int(f.read().strip())


    # --- Bank API ---

    def create_bank(self, number: int, name: str):
        bank = Bank(name=name)
        self.save_bank(number, bank)

    def save_bank(self, number: int, bank: Bank):
        try:
            # firstly save data to temp file then move to avoid corruption
            temp_path = self._get_bank_path(number).with_suffix(".tmp")
            if temp_path.exists():
                os.remove(temp_path)
            with open(temp_path, 'w') as f:
                json.dump(bank.to_dict(), f, indent=4)

            # Move temp file to final location, replace if exists
            final_path = self._get_bank_path(number)
            if final_path.exists():
                os.remove(final_path)
            temp_path.rename(final_path)
        except Exception as e:
            print(f"Error saving bank to file: {e}")

    def load_bank(self, number: int) -> Optional[Bank]:
        path = self._get_bank_path(number)
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return Bank.from_dict(json.load(f))

    def get_bank_list(self) -> List[dict]:
        banks = []
        for file in sorted(self.bank_dir.glob("*.json")):
            with open(file, 'r') as f:
                data = json.load(f)
                banks.append({
                    "number": int(file.stem),
                    "name": data.get("name", "Unnamed")
                })
        return banks

    def save_current_bank_index(self, bank_number: int):
        path = self.root / "current_bank.txt"
        with open(path, 'w') as f:
            f.write(str(bank_number))

    def load_current_bank_index(self) -> Optional[int]:
        path = self.root / "current_bank.txt"
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return int(f.read().strip())


    # --- Integrity Logic ---

    def _update_banks_on_preset_change(self, old_num: int, new_num: Optional[int]):
        """
        Scans all banks and updates references if a preset moved or was deleted.
        """
        for bank_file in self.bank_dir.glob("*.json"):
            bank_id = int(bank_file.stem)
            bank = self.load_bank(bank_id)
            
            if old_num in bank.preset_numbers:
                # Replace or Remove
                updated_list = []
                for p_num in bank.preset_numbers:
                    if p_num == old_num:
                        if new_num is not None:
                            updated_list.append(new_num)
                    else:
                        updated_list.append(p_num)
                
                bank.preset_numbers = updated_list
                self.save_bank(bank_id, bank)

    # --- App Config API ---

    def save_app_config(self, config: 'AppConfig'):
        try:
            temp_path = self.config_dir / "config.tmp"
            if temp_path.exists():
                os.remove(temp_path)
            with open(temp_path, 'w') as f:
                json.dump(config.to_dict(), f, indent=4)

            final_path = self.config_dir / "config.json"
            if final_path.exists():
                os.remove(final_path)
            temp_path.rename(final_path)
        except Exception as e:
            print(f"Error saving app config: {e}")

    def load_app_config(self) -> Optional['AppConfig']:
        path = self.config_dir / "config.json"
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return AppConfig.from_dict(json.load(f))