import os
import shutil
import uuid
import zipfile
import mmap
import re
from lxml import etree
from pathlib import Path

class ExcelUnlocker:
    def __init__(self, input_path: str, output_dir: str = "unlocked"):
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir = Path("temp") / str(uuid.uuid4())
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def unlock(self, remove_workbook=True, remove_worksheet=True, remove_vba=False) -> str:
        try:
            self._extract()
            if remove_workbook:
                self._remove_workbook_protection()
            if remove_worksheet:
                self._remove_worksheet_protection()
            if remove_vba:
                self._remove_vba_protection()
            output_path = self._repackage()
            return str(output_path)
        finally:
            self._cleanup()

    def _extract(self):
        with zipfile.ZipFile(self.input_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)

    def _remove_protection_element(self, xml_path: Path, tags: list):
        if not xml_path.exists():
            return
        tree = etree.parse(str(xml_path))
        root = tree.getroot()
        for element in list(root.iter()):
            for tag in tags:
                if tag in element.tag:
                    parent = element.getparent()
                    if parent is not None:
                        parent.remove(element)
        tree.write(str(xml_path), encoding='UTF-8', xml_declaration=True)

    def _remove_workbook_protection(self):
        workbook_xml = self.temp_dir / "xl" / "workbook.xml"
        self._remove_protection_element(workbook_xml, ["fileSharing", "workbookProtection"])

    def _remove_worksheet_protection(self):
        worksheets_dir = self.temp_dir / "xl" / "worksheets"
        if worksheets_dir.exists():
            for sheet in worksheets_dir.glob("*.xml"):
                self._remove_protection_element(sheet, ["sheetProtection"])

    def _remove_vba_protection(self):
        vba_path = self.temp_dir / "xl" / "vbaProject.bin"
        if vba_path.exists():
            with open(vba_path, "r+b") as f:
                m = mmap.mmap(f.fileno(), 0)
                m[:] = re.sub(b"DPB", b"DPx", m[:])

    def _repackage(self) -> Path:
        output_name = f"{self.input_path.stem}_unlocked{self.input_path.suffix}"
        output_path = self.output_dir / output_name

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.temp_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.temp_dir)
                    zipf.write(file_path, arcname)
        return output_path

    def _cleanup(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
