def select():
    clients = 0
    fileSelect = ""

    # Inicio
    print("Aplicacion del Servidor de Transferencia de Archivos")
    print("Aquí podrá seleccionar un archivo para enviarlo a un número determinado de clientes en simultaneo")

    # Numero de clientes
    print("Elige el numero de conexiones simultaneas con clientes")
    print("Puede haber entre 1 y 25 conexiones. Si quiere finalizar ponga 0.")
    clients = int(input())

    ready = False
    end = True
    if (clients < 26 and clients != 0):
        print("Se conectaran " + str(clients) + " clientes")
        while not ready:

            # Numero de archivo
            print("Selecciona el archivo que quieres transmitir")
            print("1- Archivo de 100 MB")
            print("2- Archivo de 250 MB")
            numFile = int(input())
            if numFile == 1:
                fileSelect = "base.xlsx"  # Verificar nombre archivo
                ready = True
            elif numFile == 2:
                fileSelect = "Capitulo.pptx"  # Verificar nombre archivo
                ready = True
            elif numFile == 0:
                ready = True
                end = True
                break
            else:
                print("Numero invalido, digite nuevamente")
            if numFile > 0 and numFile < 3:
                print("Se esperan " + str(clients) + " clientes a los que se les va a enviar " + fileSelect + " MB")

    else:
        end = True

    return clients, fileSelect
