import datetime
import subprocess
import time


def run_git_sync():
  try:
    print('Comprobando cambios en el repositorio...')
    # Ejecutar git status para ver si hay modificaciones
    status = subprocess.run(
        ['git', 'status', '--porcelain'], capture_output=True, text=True
    )

    if status.stdout.strip():
      print('Cambios detectados. Sincronizando con GitHub...')

      subprocess.run(['git', 'add', '.'], check=True)

      timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      commit_message = f'Sincronizacion automatica: {timestamp}'
      subprocess.run(['git', 'commit', '-m', commit_message], check=True)

      subprocess.run(['git', 'push', 'origin', 'main'], check=True)
      print('Sincronización automática completada con éxito.')
    else:
      print('No hay cambios nuevos que sincronizar.')
  except Exception as e:
    print(f'Error durante la sincronización: {e}')


if __name__ == '__main__':
  # Ejemplo: Ejecutar la sincronización cada 1 hora (3600 segundos)
  while True:
    run_git_sync()
    time.sleep(3600)