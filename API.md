# API — Aquí Estoy

Base de datos pública de personas reportadas. Sin autenticación requerida.

**Base URL:** `https://aquiestoy.xyz/api`

---

## Endpoints

### Descargar todos los datos

```bash
GET /personas/export?formato=json
```

**Ejemplo:**
```bash
curl "https://aquiestoy.xyz/api/personas/export?formato=json" > personas.json
```

**Respuesta:**
```json
{
  "total": 1844,
  "personas": [
    {
      "nombre": "Ana",
      "apellido": "García",
      "notas": "CI: 20003134 | Hospital: Pérez Carreño",
      "fuentes": ["https://x.com/...", "https://x.com/..."],
      "created_at": "2026-06-25T18:00:00"
    }
  ]
}
```

---

### Buscar personas

```bash
GET /personas/buscar?q=juan&limit=50
```

**Parámetros:**
- `q`: término de búsqueda (mínimo 2 caracteres)
- `limit`: máximo de resultados (default: 50)

**Ejemplo:**
```bash
curl "https://aquiestoy.xyz/api/personas/buscar?q=garcia"
```

**Respuesta:**
```json
{
  "total": 3,
  "personas": [
    {
      "id": 1,
      "nombre": "Ana",
      "apellido": "García",
      "nombre_completo": "Ana García",
      "fuentes_cantidad": 2
    }
  ]
}
```

---

### Detalle de una persona

```bash
GET /personas/<id>
```

**Ejemplo:**
```bash
curl "https://aquiestoy.xyz/api/personas/1"
```

**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Ana",
  "apellido": "García",
  "notas": "CI: 20003134 | Edad: 28",
  "fuentes": [
    {
      "id": 1,
      "url": "https://x.com/usuario/status/...",
      "descripcion": "Lista hospitalaria"
    }
  ],
  "created_at": "2026-06-25T18:00:00"
}
```

---

### Estadísticas

```bash
GET /stats
```

**Respuesta:**
```json
{
  "total_personas": 1844,
  "total_fuentes": 22,
  "status": "operativo"
}
```

---

## Ejemplos de código

### Python

```python
import requests

# Descargar todos
res = requests.get("https://aquiestoy.xyz/api/personas/export?formato=json")
personas = res.json()['personas']

print(f"Total: {len(personas)} personas")

# Buscar
res = requests.get("https://aquiestoy.xyz/api/personas/buscar", 
                   params={'q': 'juan'})
resultados = res.json()['personas']
```

### JavaScript

```javascript
// Descargar todos
const res = await fetch("https://aquiestoy.xyz/api/personas/export?formato=json");
const datos = await res.json();
const personas = datos.personas;

// Buscar
const res2 = await fetch("https://aquiestoy.xyz/api/personas/buscar?q=juan");
const resultados = await res2.json();
```

---

## Notas

⚠️ **Datos no verificados** — Consolidados de reportes en redes sociales  
⚠️ **Sin rate limiting** — Úsalo responsablemente  
⚠️ **Público** — No requiere autenticación  

---

## Licencia

Datos públicos — libre para usar con atribución.
