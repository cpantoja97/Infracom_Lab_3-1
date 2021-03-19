
## Instalar 

pip install -r requirements.txt

## Paso 1

Crear directorio Files en la ruta /Infracom_Lab_3-1/Server 
Agregar archivos de 100MB y 250MB a transferir.

## Paso 2
Modificar el archivo ServerView.py con el nombre de los archivos agregados anteriormente. Donde el primer campo en la linea 26 hace referencia al archivo de 100MB 
y el segundo campo en la linea 29 al archivo de 250MB como se indica en la figura.
![image](https://user-images.githubusercontent.com/60122434/111734832-deaf8600-8848-11eb-85e0-d279485bd0af.png)

## Paso 3

Ejecutar el codigo ServerTCP.py que se encuentra en la ruta /Infracom_Lab_3-1/Server en la maquina ubuntu que se va a utilizar para el servidor.
Seguido de esto, el programa va a solicitar que ingrese por consola un numero entre 1 y 25 para indicar el numero de conexiones simultaneas con clientes que se van a recibir. 
Una vez confirmado el numero de conexiones, se solicita por consola ingresar el numero 1 o el numero 2, para transferir el archivo de 100MB o de 250MB respectivamente.

## Paso 4

Ejecutar el codigo ClientThreads.py que se encuentra en la ruta /Infracom_Lab_3-1/Client en la maquina Windows que se va a utilizar para el cliente. 
Se debe ingresar un numero de 1 a 25 que hace referencia a el numero de clientes que van a recibir archivos simultaneamente de parte del servidor.



 
