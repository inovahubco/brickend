# 🚀 Brickend

> Infraestructura como código inteligente asistida por IA.

Brickend es una solución que acelera la creación de proyectos modernos usando **YAMLs o JSONs** para definir microservicios, páginas frontend, APIs, hooks y más. Todo el flujo está potenciado por un **agente de inteligencia artificial** que entiende lenguaje natural, genera definiciones, sugiere mejoras y ejecuta los comandos necesarios para levantar una base modular, escalable y bien estructurada.

---

## 🧱 ¿Qué incluye Brickend?

- 🧠 **Agente IA integrado** que te guía en la creación y mejora del proyecto.
- 🛠️ **CLI Brickend** que ejecuta módulos, aplica plantillas y genera código automáticamente.
- 📄 **Esquemas YAML/JSON** para definir estructuras reutilizables y versionables.
- ⚙️ **Motor de plantillas** desacoplado, modular y adaptable (v1: Supabase + Vercel).

---

## 🧩 ¿Qué puedes construir?

- CRUDs simples (ej. solo POST)
- Microservicios completos
- Interfaces frontend protegidas
- Layouts, hooks y migraciones
- Aplicaciones completas iterativas

---

## 🔁 Flujo de uso

1. **Define lo que quieres**
   - Le hablas al agente con instrucciones como: “Quiero una app de facturación con login y dashboard.”
   - El agente te pregunta detalles y crea los YAMLs correspondientes.

2. **Genera la estructura con el CLI**
   ```bash
   brickend generate microservice auth.yaml
   brickend generate crud invoices.yaml
   brickend generate frontend-section dashboard.yaml
   ```

3. **Itera y mejora**
   - El agente detecta oportunidades, sugiere módulos nuevos y refactoriza si es necesario.
   - Todo el código es versionado, modular y personalizable.

---

## 📦 Stack actual

- **Backend**: Supabase (Auth, DB, Storage, Edge Functions)
- **Frontend**: Vercel + Next.js 15 + Tailwind CSS v4 + ShadCN UI
- **CLI**: TypeScript
- **Motor de plantillas**: adaptable a múltiples tecnologías

---

## 🗺️ Ejemplo de flujo

```bash
# Usuario: Quiero manejar usuarios, roles y facturas
# Agente genera:
auth-service.yaml
users-crud.yaml
roles-crud.yaml
invoices-crud.yaml
dashboard-page.yaml

# CLI ejecuta:
brickend generate microservice auth-service.yaml
brickend generate crud users-crud.yaml
brickend generate frontend-section dashboard-page.yaml
```

---

## 🧩 Próximamente

- ☁️ Soporte multi-stack: Firebase, PlanetScale, etc.
- 🤝 Modo colaborativo multiusuario
- 🧾 Lógica de negocio intermedia asistida por IA

---

## 📚 Documentación y recursos

- [Guía de YAMLs](docs/yamls.md) (próximamente)
- [Templates base](templates/)
- [Ejemplos de uso](examples/)

---

## 🧠 Contribuye

¿Tienes ideas, módulos o plantillas útiles? ¡Ayúdanos a expandir Brickend!

---

> Hecho con ⚡ por desarrolladores para desarrolladores. Tu infraestructura, más rápida y más inteligente.
