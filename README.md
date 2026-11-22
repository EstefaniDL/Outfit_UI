# Estudio de Outfits — Interfaz Web y Motor de Recomendación

Interfaz web responsiva desacoplada del pipeline de etiquetado, limpieza y modelado, diseñada para:
- **Inicio de sesión y clóset persistente por usuario (`user_id`):** evita que el usuario tenga que volver a subir sus fotos cada vez que entra.
- **Revisión y corrección de etiquetas:** permite ajustar atributos mientras se afina el modelo y el etiquetado.
- **Recomendación curada y variada:** evalúa combinaciones bajo reglas de colorimetría, contraste, formalidad, ocasión, clima, capas y proporciones, mostrando opciones seleccionadas (no el universo bruto de combinaciones) y una descripción contextual de para qué funciona cada outfit.
- **Preparación para la nube:** organiza los datos por `user_id` para facilitar la migración hacia *Cloud Storage* y una tabla de usuarios/prendas.

## Estructura del proyecto

- `backend/adapter_modelo.py`: contrato `Prenda` y función `adaptar_prediccion_externa` para conectar el módulo/JSON/CSV de etiquetas o predicciones cuando esté listo.
- `backend/storage_service.py`: almacenamiento estructurado por `user_id` para la demo, listo para evolucionar a *Cloud Storage* y base de datos.
- `backend/rules_engine.py`: evaluación de reglas y selección curada de outfits con descripción contextual.
- `backend/app.py`: endpoints de sesión, clóset, subida/edición/eliminación de prendas y recomendación.
- `frontend/`: interfaz web responsiva (`index.html`, `styles.css`, `app.js`).
- `Dockerfile`: empaquetado para despliegue en la nube (por ejemplo, Cloud Run o plataformas similares).
