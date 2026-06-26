# Aquí Estoy

Base de datos consolidada de personas reportadas tras el terremoto en Venezuela (junio 2026).

**Sitio:** https://aquiestoy.xyz  
**API:** https://aquiestoy.xyz/api

---

## Obtener los datos

### Descargar completo (JSON)

```bash
curl "https://aquiestoy.xyz/api/personas/export?formato=json" > personas.json
```

### En Python

```python
import requests

res = requests.get("https://aquiestoy.xyz/api/personas/export?formato=json")
datos = res.json()

print(f"Total: {datos['total']} personas")
for p in datos['personas']:
    print(f"  {p['nombre']} {p['apellido']}")
```

### Formato

```json
{
  "total": 1844,
  "personas": [
    {
      "nombre": "Ana",
      "apellido": "García",
      "notas": "CI: 20003134 | Edad: 28 | Hospital: Pérez Carreño",
      "fuentes": ["https://x.com/...", "https://x.com/..."],
      "created_at": "2026-06-25T18:00:00"
    }
  ]
}
```

---

## Buscar personas específicas

```bash
curl "https://aquiestoy.xyz/api/personas/buscar?q=juan"
```

---

## Documentación completa

Ver [API.md](API.md) para todos los endpoints y ejemplos.

---

## Contribuir datos

¿Encontraste una nueva lista? Abre un issue o contacta vía GitHub.

---

## Licencia

Datos públicos — libre para usar con atribución.
