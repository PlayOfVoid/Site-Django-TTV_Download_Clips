import os
import re
import subprocess
import uuid  # Для создания уникальных имен файлов
import urllib.parse
import logging  # Для логирования

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.urls import reverse

from .forms import TwitchClipForm

# Получаем логгер
logger = logging.getLogger(__name__)

def generate_safe_filename(filename):
    """Генерирует безопасное имя файла."""
    # Заменяем небезопасные символы на дефисы
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", filename)
    # Обрезаем длину
    return safe_name[:100]


def download_clip(request):
    if request.method == 'POST':
        form = TwitchClipForm(request.POST)
        if form.is_valid():
            clip_url = form.cleaned_data['clip_url']
            quality = form.cleaned_data['quality']

            match = re.search(r"clip/(?P<clip_slug>[^?]+)", clip_url)
            if not match:
                return render(request, 'downloader/download_form.html', {
                    'form': form,
                    'error': 'Invalid Twitch clip URL.'
                })

            clip_slug = match.group("clip_slug")

            # 1. Создаем уникальное имя файла (используя UUID)
            unique_id = uuid.uuid4()
            filename = f"{generate_safe_filename(clip_slug)}_{quality}_{unique_id}.mp4"
            filepath = os.path.join(settings.DOWNLOAD_DIR, filename)

            try:
                streamlink_command = [
                    "streamlink",
                    clip_url,
                    quality,
                    "-o",
                    filepath,
                ]
                result = subprocess.run(streamlink_command, check=True, capture_output=True, text=True)

                # 2. Создаем URL для загрузки (используя имя файла)
                download_url = reverse('serve_download', kwargs={'filename': filename})
                return render(request, 'downloader/download_success.html', {'download_url': download_url})

            except subprocess.CalledProcessError as e:
                # Выводим e.stderr в консоль для отладки
                print(f"Streamlink Error (stderr):\n{e.stderr}")

                # Отображаем общее сообщение об ошибке пользователю
                return render(request, 'downloader/download_form.html', {
                    'form': form,
                    'error': "Error downloading clip. Please try again later."
                })
    else:
        form = TwitchClipForm()
    return render(request, 'downloader/download_form.html', {'form': form})

def serve_download(request, filename):
    """Безопасная отдача скачанного файла."""
    file_path = os.path.join(settings.DOWNLOAD_DIR, filename)

    # 1.  Проверяем, что файл существует (для дополнительной безопасности)
    if not os.path.exists(file_path):
         raise Http404("File not found")

    # 2.  Отдаем файл (с обработкой ошибок)
    try:
        response = FileResponse(open(file_path, 'rb'), as_attachment=True)
        # Устанавливаем безопасное имя файла для скачивания
        safe_filename = urllib.parse.quote(filename)
        response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        return response
    except FileNotFoundError:
        raise Http404("File not found")
    except OSError:
        raise Http404("File access error")