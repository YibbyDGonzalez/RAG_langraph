#!/bin/bash
# Arranca el servidor Ollama en segundo plano
ollama serve &

# Espera a que el servidor este listo
echo "Esperando a que Ollama arranque..."
until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
  sleep 1
done

# Descarga el modelo solo si no esta ya en el volumen
if ! ollama list 2>/dev/null | grep -q "llama3.2:1b"; then
  echo "Primera ejecucion: descargando llama3.2:1b (~1.3 GB)..."
  ollama pull llama3.2:1b
  echo "Modelo descargado y listo."
else
  echo "Modelo llama3.2:1b ya esta disponible."
fi

# Mantiene el proceso servidor activo
wait
