# M3.con

Aplicativo para buscar a prévia de um vídeo do YouTube e converter o áudio para MP3. A interface é feita em Tkinter e o download usa yt-dlp.

Use o aplicativo somente com conteúdo que você tenha autorização para baixar. Confira também os termos da plataforma e as leis aplicáveis.

## Baixar para Windows

Baixe a versão atual na [página de Releases](https://github.com/Artthursantos/M3.con/releases). Na `v1.0.0`, escolha um dos pacotes:

### M3.con Windows Leve

Este pacote contém o aplicativo, mas não inclui o FFmpeg. Ele é menor e serve para computadores que já têm o FFmpeg instalado.

1. Baixe o [M3.con Windows Leve](https://github.com/Artthursantos/M3.con/releases/download/v1.0.0/M3.con-Windows-Leve.zip).
2. Extraia todos os arquivos para uma pasta. Não execute o aplicativo de dentro do ZIP.
3. Abra `M3.con.exe` com dois cliques.
4. Se o FFmpeg não estiver instalado, abra o Terminal e execute `winget install ffmpeg`.
5. Depois que a instalação terminar, feche e abra o M3.con novamente.

### M3.con Windows Portátil

Este pacote inclui o FFmpeg necessário para a conversão. É maior, mas não precisa de Python nem de uma instalação separada do FFmpeg.

1. Baixe o [M3.con Windows Portátil](https://github.com/Artthursantos/M3.con/releases/download/v1.0.0/M3.con-Windows-Portatil.zip).
2. Extraia todos os arquivos para uma pasta. Mantenha `M3.con.exe` e a pasta `ffmpeg` juntos.
3. Abra `M3.con.exe` com dois cliques.

Ambas as versões precisam de conexão com a internet para consultar e baixar vídeos. O Windows pode exibir o SmartScreen porque o aplicativo não tem assinatura digital; só execute uma cópia obtida na página oficial do projeto.

### Usar o aplicativo

1. Cole um link de vídeo do YouTube.
2. Aguarde a prévia aparecer.
3. Escolha uma pasta de destino.
4. Clique em **Baixar e converter** e aguarde a conclusão.

## Executar pelo código-fonte

Requisitos: Windows 10 ou posterior, Python 3.9 ou posterior e FFmpeg no `PATH`.

```powershell
python --version
ffmpeg -version
python -m pip install -r requirements.txt
python main.py
```

Se `python` não for reconhecido, instale o Python de [python.org](https://www.python.org/downloads/) e marque **Add Python to PATH**. Para instalar o FFmpeg no Windows, use `winget install ffmpeg` e reabra o terminal.

Linux/macOS também podem executar a versão-fonte se Python com Tkinter e FFmpeg estiverem instalados. A distribuição `.exe` é apenas para Windows.

## Estrutura do projeto

- `main.py`: código do aplicativo.
- `requirements.txt`: dependências Python.
- `LICENSE`: licença MIT do código do M3.con.
- `assets/icons/`: ícones do aplicativo e do histórico.
- `dist/M3.con.exe`: versão leve compilada.
- `dist/M3.con-Windows-Leve.zip`: pacote leve para publicar em Releases.
- `dist/M3.con-Windows-Portatil.zip`: pacote portátil para publicar em Releases.
- `dist/versoes-antigas/`: builds de testes anteriores, não publicar.
- `build/`: arquivos temporários do empacotamento.

## Avisos do FFmpeg

O código do M3.con está sob a licença MIT; veja o arquivo `LICENSE`. Essa licença não altera as licenças das dependências incluídas no executável.

O pacote portátil inclui a build Essentials do FFmpeg 9.0.2, fornecida por [gyan.dev](https://www.gyan.dev/ffmpeg/builds/). Essa build é licenciada sob GPLv3. O pacote portátil inclui o arquivo de licença e o README original da build, com configuração, versão e referência ao código-fonte correspondente: [FFmpeg 9.0.2](https://github.com/FFmpeg/FFmpeg/commit/946fcce07b).

O código-fonte deste aplicativo não inclui o FFmpeg; a build é distribuída separadamente no ZIP portátil. Consulte os avisos incluídos nesse pacote antes de redistribuí-lo.

## Preparar uma Release no GitHub

1. Envie o código-fonte e os arquivos do projeto ao repositório, sem enviar `.venv`, `.venv-1`, `build` ou `dist/versoes-antigas`.
2. Crie uma **Release** no GitHub associada a uma tag de versão, por exemplo `v1.0.0`.
3. Anexe `M3.con-Windows-Leve.zip` e `M3.con-Windows-Portatil.zip` à Release.
4. Na descrição, explique que a versão leve requer FFmpeg instalado e que a portátil já o inclui.

Não é preciso colocar os ZIPs grandes no histórico do código: publique-os como anexos da Release.
