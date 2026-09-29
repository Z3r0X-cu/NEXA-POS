# NEXA POS 3.0.0

Sistema de punto de venta local escrito íntegramente en Python 3 con PyQt6, SQLite y ReportLab. Diseñado para funcionar localmente en Windows y Linux.

## Información

- Nombre: NEXA POS
- Versión: 3.0.0
- Creador: Z3r0X
- Código fuente: https://github.com/Z3r0X-cu/NEXA-POS
- Lenguaje: Python 3
- Interfaz: PyQt6
- Base de datos: SQLite
- Comprobantes y reportes: ReportLab

## Acceso inicial

Si la base de datos no contiene usuarios, la aplicación crea automáticamente:

- Usuario: `admin`
- Contraseña: `admin1234`
- Rol: `admin`

El administrador puede modificar posteriormente la configuración y los usuarios desde el módulo de Administración.

## Funciones principales

- Roles: admin, almacenero, economia y vendedor.
- Gestión de productos, categorías, stock y fotografías.
- Registro de facturas de entrada independientes para cada compra.
- Conservación del precio de compra y precio de venta exactos de cada factura.
- Stock acumulado solamente por la cantidad realmente adquirida en cada factura.
- Control de lotes de costo mediante las facturas para calcular la ganancia de las ventas.
- Emisión de comprobantes PDF numerados por venta.
- Pago en efectivo o transferencia.
- Registro de foto de la transferencia, número de tarjeta y datos principales del pagador.
- Cierre diario con ventas, ganancia y números de comprobantes emitidos.
- Cuadre mensual programado para el día 28, integrando ventas, cuadres diarios y facturas de entrada.
- Fecha y hora en tiempo real dentro de la ventana principal.
- Cerrar sesión devuelve al login sin cerrar la aplicación.
- Botón independiente Salir para cerrar la aplicación.
- Logo de NEXA POS en login, interfaz principal y documentos PDF.
- Diálogo Acerca de con versión, creador, tecnologías y repositorio.
- Eliminación segura de productos mediante archivado lógico para conservar históricos y evitar errores de claves foráneas.

## Regla de facturas y stock

Una segunda factura del mismo producto nunca modifica ni sobrescribe la factura anterior. Cada entrada queda registrada como una fila independiente en `invoices` con su número, proveedor, cantidad, precio de compra, precio de venta, comprobante y fecha.

El stock del producto solamente aumenta por la cantidad de la nueva factura. El precio histórico de compra no se utiliza para sobrescribir el precio de compra de `products`.

Para las ventas, NEXA POS utiliza los lotes de factura disponibles y descuenta primero las unidades de las facturas más antiguas. De esta forma, el costo utilizado para calcular la ganancia corresponde al precio de compra registrado en cada factura.

## Eliminación de productos

Los productos que ya aparecen en facturas o ventas no se borran físicamente de SQLite porque hacerlo destruiría el historial y provocaría errores de integridad referencial. El botón `Eliminar` los marca como inactivos y dejan de aparecer en el catálogo y en el inventario operativo, mientras sus facturas y ventas permanecen disponibles para los cierres.

## Cierre diario

El cierre diario genera un PDF con:

- Total de ventas del día.
- Ganancia del día.
- Vendedor de cada operación.
- Hora de cada venta.
- Número de cada comprobante emitido.

El cierre se registra en `daily_closes` para formar parte del cuadre mensual.

## Cuadre mensual

El botón de cuadre mensual se encuentra en Economía. El proceso está programado para ejecutarse el día 28 de cada mes y reúne:

- Ventas realizadas durante el mes.
- Ganancia de las ventas.
- Cuadres diarios registrados.
- Números de comprobantes.
- Facturas de entrada al stock.
- Cantidades adquiridas.
- Precios de compra de las facturas.
- Precios de venta registrados en las facturas.
- Proveedores/orígenes de las entradas.

El resultado se guarda como PDF y se registra en `monthly_closes`.

## Pagos por transferencia

Al procesar una venta se puede seleccionar `TRANSFERENCIA`. Para este método se registra:

- Número de tarjeta.
- Nombre del pagador.
- CI.
- Teléfono.
- Dirección.
- Foto del comprobante de la transacción.

La información queda asociada a la venta y también aparece en el comprobante cuando corresponde.

## Base de datos

SQLite se mantiene con `PRAGMA foreign_keys = ON`. Las migraciones de esta versión agregan las estructuras necesarias sin eliminar las tablas existentes.

## Instalación

Instalar Python 3 y las dependencias:

```bash
pip install PyQt6 reportlab Pillow
```

Ejecutar:

```bash
python main.py
```

En Linux, si el sistema usa un entorno gráfico compatible con Qt, la aplicación funciona de forma local sin servidor web.

## Archivos principales

- `main.py`: inicio de la aplicación, login y ciclo de ventanas.
- `config.py`: versión, rutas, nombre, creador y configuración general.
- `database.py`: esquema SQLite y migraciones.
- `views/login_view.py`: autenticación.
- `views/main_window.py`: ventana principal, reloj, sesión, salida y Acerca de.
- `views/almaceno_view.py`: inventario y archivado de productos.
- `views/economia_view.py`: facturas de entrada, cierre diario y cuadre mensual.
- `views/ventas_view.py`: carrito, ventas y pagos por transferencia.
- `views/admin_view.py`: administración de usuarios y negocio.
- `utils/pdf_generator.py`: comprobantes y reportes PDF.
- `utils/security.py`: funciones PBKDF2 existentes del proyecto.
- `utils/image_utils.py`: procesamiento de imágenes.

## Actualización 3.0.0

- Versión global actualizada a 3.0.0.
- Contraseña inicial solicitada actualizada a `admin1234` para instalaciones nuevas.
- Logo incorporado desde `logo.png`.
- Enter funcional en el login.
- Reloj de fecha y hora en tiempo real.
- Cerrar Sesión separado de Salir.
- Diálogo Acerca de.
- Facturas de compra independientes por entrada.
- Precios históricos conservados por factura.
- Costos de venta calculados desde lotes de factura.
- Archivado lógico de productos para evitar `FOREIGN KEY constraint failed`.
- Cierre diario simplificado a ventas, ganancias y comprobantes.
- Cuadre mensual con ventas, cuadres diarios y entradas de stock.
- Pagos por transferencia con fotografía y datos del pagador.
- Logo incorporado a los PDF.

## Nota de compatibilidad

La interfaz existente se conserva y los cambios se incorporan alrededor de los controles ya existentes. La base de datos utiliza migraciones para instalaciones que ya tenían una versión anterior de NEXA POS.

Antes de actualizar una instalación con datos reales, se recomienda utilizar la función de exportación de base de datos existente y conservar una copia de `nexa.db`.
