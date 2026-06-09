# 🌐 WebGrabber

Downloader de arquivos web com interface gráfica, inspirado no clássico **WebReaper**. Escaneia uma página e baixa automaticamente os arquivos pelos tipos selecionados.

---

## Interface

Janela de **900×700 px**, centralizada na tela, com tema escuro em tons de azul-marinho (`#1a1a2e`, `#16213e`, `#0f3460`) e destaque vermelho (`#e94560`). A interface é dividida em cards:

| Card | Função |
|------|--------|
| 🔗 URL da Página | Campo para digitar o endereço da página a escanear |
| 📁 Tipos de Arquivo | Grid de checkboxes para selecionar categorias |
| 💾 Diretório de Saída | Caminho de destino dos downloads, com botão "Procurar..." |
| 📋 Arquivos Encontrados | Lista rolável com checkbox individual por arquivo |

---

## Tipos de Arquivo Suportados

| Categoria | Extensões | Padrão |
|-----------|-----------|--------|
| 📄 PDF | `.pdf` | ✅ ativo |
| 🖼️ Imagens | `.jpg` `.jpeg` `.png` `.gif` `.webp` `.svg` `.bmp` `.ico` `.tiff` | ✅ ativo |
| 📦 Compactados | `.zip` `.rar` `.7z` `.tar` `.gz` `.tar.gz` `.tgz` `.bz2` | ✅ ativo |
| 📝 Documentos | `.doc` `.docx` `.odt` `.txt` `.rtf` | ☐ inativo |
| 📊 Planilhas | `.xls` `.xlsx` `.csv` `.ods` | ☐ inativo |
| 🎵 Áudio | `.mp3` `.wav` `.ogg` `.flac` `.aac` `.wma` `.m4a` | ☐ inativo |
| 🎬 Vídeo | `.mp4` `.avi` `.mkv` `.webm` `.mov` `.wmv` `.flv` `.m4v` | ☐ inativo |
| ⚙️ Executáveis | `.exe` `.msi` `.deb` `.rpm` `.dmg` `.appimage` | ☐ inativo |
| 📎 Outros | Campo livre separado por vírgula (padrão: `.bin, .iso`) | ☐ inativo |

---

## Funcionalidades

- **Escaneamento multifonte** — busca links nas tags `<a href>`, `<img src>`, `<source src>`, atributos `srcset` e `data-src` (lazy loading)
- **User-Agent real** — simula o Chrome para evitar bloqueios de servidor
- **Download em streaming** — transfere em chunks de 8 KB, mantendo baixo uso de memória
- **Renomeação automática** — evita sobrescrever arquivos com mesmo nome (`arquivo_1.pdf`, `arquivo_2.pdf`...)
- **Hover tooltip** — passar o mouse sobre um arquivo exibe a URL completa na barra de status
- **Seleção rápida** — botões "Selecionar Todos" e "Desmarcar Todos"
- **Interrupção a qualquer momento** — botão "Parar" encerra o download com segurança
- **Threads dedicadas** — scan e download rodam em background, mantendo a interface responsiva
- **Diretório padrão** — `~/Downloads/WebGrabber`, criado automaticamente se não existir

---

## Requisitos

```bash
pip install requests beautifulsoup4
```

> Python 3.x com `tkinter` (incluso na instalação padrão do Python no Windows).

---

## Como usar

```bash
python webgrabber.py
```

1. Cole a URL da página no campo superior
2. Marque os tipos de arquivo desejados
3. Clique em **Escanear Página**
4. Selecione os arquivos da lista
5. Clique em **Baixar Selecionados**
