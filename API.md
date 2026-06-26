# API — Aquí Estoy

API pública para acceder a la base de datos de personas reportadas durante la emergencia en Venezuela.

**Base URL:** `https://aquiestoy.xyz/api`

**Contexto:** Esta API consolida listas de personas heridas, desaparecidas e incomunicadas reportadas en redes sociales tras el terremoto de junio 2026. Facilita la búsqueda digital para familias y desarrolladores.

---

## Endpoints

### 1. Estadísticas (`/stats`)

Obtén el estado actual de la base de datos.

```bash
curl https://aquiestoy.xyz/api/stats
```

**Respuesta:**
```json
{
  "total_personas": 1844,
  "total_fuentes": 22,
  "ultima_actualizacion": {
    "persona": "2026-06-26T05:46:36.417038",
    "fuente": "2026-06-26T05:46:34.944086"
  },
  "status": "operativo"
}
```

---

### 2. Buscar Personas (`/personas/buscar`)

Busca por nombre o apellido.

```bash
# Búsqueda simple
curl "https://aquiestoy.xyz/api/personas/buscar?q=juan"

# Con límite de resultados
curl "https://aquiestoy.xyz/api/personas/buscar?q=garcia&limit=20"
```

**Parámetros:**
- `q` (requerido): término de búsqueda, mínimo 2 caracteres
- `limit` (opcional): máximo de resultados a retornar (default: 50)

**Respuesta:**
```json
{
  "total": 3,
  "personas": [
    {
      "id": 1,
      "nombre": "Juan",
      "apellido": "García",
      "nombre_completo": "Juan García",
      "fuentes_cantidad": 2
    }
  ]
}
```

---

### 3. Detalle de Persona (`/personas/<id>`)

Obtén información completa de una persona con TODAS sus fuentes.

```bash
curl https://aquiestoy.xyz/api/personas/1
```

**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Milagros",
  "apellido": "Jiménez",
  "nombre_completo": "Milagros Jiménez",
  "notas": "Edad: 45. Procedencia: Los Frailes",
  "created_at": "2026-06-25T17:55:10.602943",
  "fuentes": [
    {
      "id": 1,
      "url": "https://x.com/jesusmedinae/status/2070069298471587929",
      "descripcion": "Lista hospitalaria Periférico de Catia",
      "created_at": "2026-06-25T17:54:26.959312"
    },
    {
      "id": 5,
      "url": "https://x.com/otro/status/...",
      "descripcion": "Otra fuente",
      "created_at": "2026-06-25T18:00:00"
    }
  ],
  "fuentes_cantidad": 2
}
```

---

### 4. Exportar Personas (`/personas/export`)

Descarga todas las personas en CSV o JSON.

```bash
# CSV (por defecto)
curl https://aquiestoy.xyz/api/personas/export > personas.csv

# JSON
curl "https://aquiestoy.xyz/api/personas/export?formato=json" > personas.json
```

**Parámetros:**
- `formato` (opcional): `csv` o `json` (default: `csv`)

**CSV Output:**
```
nombre,apellido,notas,fuentes
Milagros,Jiménez,"Edad: 45",https://x.com/... | https://x.com/...
```

**JSON Output:**
```json
{
  "total": 1844,
  "personas": [
    {
      "nombre": "Milagros",
      "apellido": "Jiménez",
      "notas": "Edad: 45",
      "fuentes": [
        "https://x.com/..."
      ],
      "created_at": "2026-06-25T17:55:10.602943"
    }
  ]
}
```

---

### 5. Listar Fuentes (`/fuentes`)

Obtén información de todas las fuentes de datos.

```bash
curl https://aquiestoy.xyz/api/fuentes
```

**Respuesta:**
```json
{
  "total": 22,
  "fuentes": [
    {
      "id": 1,
      "url": "https://x.com/jesusmedinae/status/2070069298471587929",
      "descripcion": "Lista hospitalaria Periférico de Catia — heridos La Guaira",
      "personas_cantidad": 52,
      "created_at": "2026-06-25T17:54:26.959312"
    }
  ]
}
```

---

## Ejemplos por Lenguaje

### cURL

```bash
# Buscar
curl "https://aquiestoy.xyz/api/personas/buscar?q=juan"

# Descargar JSON
curl "https://aquiestoy.xyz/api/personas/export?formato=json" | jq .
```

### Python

```python
import requests
import json

# Buscar personas
response = requests.get('https://aquiestoy.xyz/api/personas/buscar', 
                       params={'q': 'juan', 'limit': 10})
personas = response.json()['personas']

for p in personas:
    print(f"{p['nombre']} {p['apellido']} — {p['fuentes_cantidad']} fuentes")

# Obtener detalle
persona_id = personas[0]['id']
response = requests.get(f'https://aquiestoy.xyz/api/personas/{persona_id}')
detalle = response.json()

print(f"Reportado en: {[f['descripcion'] for f in detalle['fuentes']]}")

# Descargar todo
response = requests.get('https://aquiestoy.xyz/api/personas/export',
                       params={'formato': 'json'})
with open('personas.json', 'w') as f:
    json.dump(response.json(), f, indent=2, ensure_ascii=False)
```

### JavaScript

```javascript
// Buscar
async function buscar(nombre) {
  const response = await fetch(
    `https://aquiestoy.xyz/api/personas/buscar?q=${encodeURIComponent(nombre)}`
  );
  const data = await response.json();
  return data.personas;
}

// Obtener detalle
async function obtenerPersona(id) {
  const response = await fetch(`https://aquiestoy.xyz/api/personas/${id}`);
  return response.json();
}

// Uso
const resultados = await buscar('juan');
console.log(`Encontrados: ${resultados.length}`);

if (resultados.length > 0) {
  const detalle = await obtenerPersona(resultados[0].id);
  console.log(`Reportado en ${detalle.fuentes.length} fuentes:`);
  detalle.fuentes.forEach(f => console.log(`  - ${f.descripcion}`));
}
```

### React

```jsx
import { useState, useEffect } from 'react';

export function BuscadorPersonas() {
  const [query, setQuery] = useState('');
  const [resultados, setResultados] = useState([]);
  const [loading, setLoading] = useState(false);

  const buscar = async (q) => {
    if (q.length < 2) return;
    setLoading(true);
    const resp = await fetch(
      `https://aquiestoy.xyz/api/personas/buscar?q=${encodeURIComponent(q)}`
    );
    const data = await resp.json();
    setResultados(data.personas);
    setLoading(false);
  };

  useEffect(() => {
    const timer = setTimeout(() => buscar(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <>
      <input
        placeholder="Buscar persona..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {loading && <p>Buscando...</p>}
      <ul>
        {resultados.map(p => (
          <li key={p.id}>
            {p.nombre_completo} ({p.fuentes_cantidad} fuentes)
          </li>
        ))}
      </ul>
    </>
  );
}
```

---

## Casos de Uso

### 1. Integración en Sitio Web

```html
<form id="buscar-form">
  <input type="text" id="query" placeholder="Buscar persona...">
</form>
<div id="resultados"></div>

<script>
document.getElementById('buscar-form').onsubmit = async (e) => {
  e.preventDefault();
  const q = document.getElementById('query').value;
  const res = await fetch(`/api/personas/buscar?q=${q}`);
  const data = await res.json();
  
  const html = data.personas.map(p => 
    `<div>${p.nombre_completo}</div>`
  ).join('');
  
  document.getElementById('resultados').innerHTML = html;
};
</script>
```

### 2. Bot de Telegram/Discord

```python
import requests

def buscar_persona(nombre):
    response = requests.get('https://aquiestoy.xyz/api/personas/buscar',
                           params={'q': nombre, 'limit': 5})
    personas = response.json()['personas']
    
    if not personas:
        return "No encontrado"
    
    msg = f"Encontrados {len(personas)} resultado(s):\n"
    for p in personas:
        msg += f"• {p['nombre_completo']} ({p['fuentes_cantidad']} reportes)\n"
    
    return msg
```

### 3. Sincronización Periódica

```python
import requests
import json
from datetime import datetime

# Descargar todos los datos cada hora
response = requests.get('https://aquiestoy.xyz/api/personas/export',
                       params={'formato': 'json'})
data = response.json()

with open(f'backup_{datetime.now().isoformat()}.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False)

print(f"Descargadas {data['total']} personas")
```

---

## Notas Importantes

⚠️ **Sin autenticación:** La API es pública sin credenciales requeridas.

⚠️ **Emergencia humanitaria:** Estos datos son consolidados de reportes en redes sociales. No son verificados oficialmente. Úsalos como referencia.

⚠️ **Rate limiting:** No hay límites de velocidad actualmente. Úsalo responsablemente.

⚠️ **Actualizaciones:** Los datos se actualizan continuamente. Sincroniza periódicamente si necesitas datos frescos.

---

## Licencia

Datos públicos recopilados durante emergencia humanitaria. Libre para usar con atribución.

**Attributión sugerida:**
> Datos de Aquí Estoy — Base de datos consolidada de personas reportadas tras terremoto Venezuela 2026

---

## Problemas o Sugerencias

Contacta vía:
- GitHub: [rypptc/aquiestoy](https://github.com/rypptc/aquiestoy)
- Twitter: [@aquiestoy](https://twitter.com)
- Email: [contacto]

---

**Última actualización:** 2026-06-26
