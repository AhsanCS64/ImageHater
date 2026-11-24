# Build a windowed Windows distribution with its native libraries alongside it.
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("pikepdf")
a = Analysis(["ScanPDF.pyw"], datas=datas, binaries=binaries,
             hiddenimports=hiddenimports + ["PIL.PdfImagePlugin", "PIL.JpegImagePlugin"])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="ScanPDF",
          console=False, upx=False)
app = COLLECT(exe, a.binaries, a.datas, upx=False, name="ScanPDF")
