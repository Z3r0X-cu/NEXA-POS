# NEXUS POS - Sistema de Punto de Venta Cyberpunk

Sistema de Punto de Venta (POS) local multiplataforma escrito en Python 3 con interfaz estilizada PyQt6 Cyberpunk Neon, diseñado para funcionar aisladamente en entornos Windows y Linux.

## 🚀 Características
- **Multi-Rol Estricto**:
  - `Admin`: Control total del sistema, gestión de usuarios, categorías y backup de base de datos.
  - `Almacenero`: Gestión completa de inventario, codificación de productos y manejo de atributos físicos.
  - `Economía`: Alta de facturas de compra, determinación de márgenes y precios de venta.
  - `Vendedor`: Interfaz de facturación limpia, consulta de stock y emisión de comprobantes en **PDF**.
- **Seguridad**: Hash de contraseñas mediante **PBKDF2-HMAC-SHA256**.
- **Base de Datos Local y Portabilidad**: Persistencia sobre **SQLite** con funciones integradas de exportación e importación de la base de datos completa.
- **Generación de Comprobantes**: Emisión de facturas/recibos listos para impresión mediante ReportLab.

## 📦 Instalación

1. **Clonar el repositorio / Descomprimir ZIP**:
```bash
git clone [https://github.com/tu-usuario/nexus-pos.git](https://github.com/tu-usuario/nexus-pos.git)
cd nexus-pos
