

## Windows

- install [Tesseract-OCR](https://github.com/tesseract-ocr) from [this](https://github.com/UB-Mannheim/tesseract/wiki)
- install python dependences
- install poppler ([information source](https://stackoverflow.com/questions/18381713/how-to-install-poppler-on-windows))
    - download from [this](http://blog.alivate.com.au/poppler-windows/)
    - extract to some folder `<poppler_root>`
    - add `<poppler_root>/bin` into system environment variable `PATH`
- execute `python atexter_bot.py` to create default `conf.yaml` and `access.yaml`
- specify bot token into `bot.token` section of `conf.yaml`
- add path of tesseract.exe into `tesseract.cmd` section of `conf.yaml`
    ```yaml
    tesseract:
      cmd: 'C:\Program Files\Tesseract-OCR\tesseract.exe'
    ```
- create run.cmd script, example of `run.cmd` script to run bot in background (uses `pythonw.exe` instead of `python.exe`)
    ```Batch
    cmd /k "cd /d D:\prod\a.texter_bot\venv\Scripts & activate & cd /d D:\prod\a.texter_bot & pythonw.exe atexter_bot.py"
    ```
- run