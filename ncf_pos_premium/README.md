**Configuracion modulo ncf_pos_premiun para Odoo 10.0**

1-Instalar redis [link](https://redis.io)
2-En el archivo de configuración de odoo se debe de colocar las siguientes opciones:

    server_wide_modules = telegram,web,web_kanban,queue_job
    [queue_job]
    channels = root:2,pos:1,poscache:1

3-Debe tener agregado a su addons path el modulo queue_job que se encuentra en el  repo https://github.com/MarcosCommunity/marcos_community_addons el branch 10.0 que lo contiene
4-Instalar modulo ncf_pos_premium 
5-En Punto de venta/configuracion/Puntos de venta debe configurar en todos los puntos de ventas siguientes opciones.

A - Cliente de contado: Sera el cliente que el punto de venta usara por defecto si no selecciona uno de no configurar siempre medra que elegir uno.
B-En la sección Multi-session debe crear un nombre en campo Multi-session: Esto sirve para que los puntos de ventas se mantengan sincronizados.

> Ejemplo: Si va a implementar dos sucursales diferentes deberá crear un Multi-session llamado Tienda A y todos los puntos de ventas que succionen e una misma sucursal deberán utilizar este multi-session y para la otra suscursale crearía el Tienda B y asi sucesivamente por cuantas sucursales tenga que implementar.

4-Configuracion redis del lado de Odoo: como redis en un motos de base de datos en memoria este identifica las bases de datos por un numero entero y debemos especificar cual es la que usara para la Base de datos odoo de que estamos configurando. para esto activamos el modo de desarrollador y en configracion/Tecnico/Paramtros/Parametros del sistema asignamos a la propiedad redis_db_pos_cache el numero entero correspondiente a la base de datos de redis que usara para la base de datos de Odoo que esta configurando.

> Ejemplo: Si tiene una instancia de odoo donde sirve varias base de datos deberá asignar un numero diferente para cada una de ellas 
> DB1= redisdb 1
> DB2-redisdb 2
> ETC...

5-Job queue configuration: /Job queue/queue/channels debar crear los canales.

![enter image description here](https://scontent.fsdq1-2.fna.fbcdn.net/v/t31.0-8/22904678_1891776707500895_2788205143809822974_o.jpg?oh=9df81617c47ade9ce8fc35d8cb1d5997&oe=5AA97903)

![enter image description here](https://scontent.fsdq1-2.fna.fbcdn.net/v/t31.0-8/22861413_1891776700834229_5528953907400395403_o.jpg?oh=1ef75c75693e92975f738a506aa5d2fe&oe=5A66966D)

> la funcionalidad de este modulo es entregar la facturar de inmediato en el pos y la ejecución de creaciones de la factura , conduce, pago y conciliación del pago de la factura se ejecute en segundo plano para que el cliente no tenga que esperar.

6-Primera carga de productos y clientes desde la base de datos de odoo a redis, deberá ejecutar el cron job de odoo destinado para esto solo la primera vez. En mode developer /configuracion/tecnico/Automatizacion/Acciones planificadas el cron con el nombre [POS] Cache Datas .

Listo disfrutelo !!!



