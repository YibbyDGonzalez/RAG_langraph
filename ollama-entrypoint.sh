#!/bin/bash
# Arranca el servidor Ollama en segundo plano
ollama serve &

# Espera a que el servidor esté listo
echo "Esperando a que Ollama arranque..."
until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
  sleep 1
done

# Descarga el modelo solo si no está ya en el volumen
if ! ollama list 2>/dev/null | grep -q "llama3.2:3b"; then
  echo "Primera ejecución: descargando llama3.2:3b (~2 GB)..."
  ollama pull llama3.2:3b
  echo "Modelo descargado y listo."
else
  echo "Modelo llama3.2:3b ya está disponible."
fi

# Mantiene el proceso servidor activo
wait
