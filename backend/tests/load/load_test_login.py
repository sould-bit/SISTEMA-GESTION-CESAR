from locust import HttpUser, task, between

class ApiUser(HttpUser):
    """
    Usuario de prueba de carga para la API de FastOps.
    Simula el comportamiento de un usuario iniciando sesión.
    """
    # Tiempo de espera entre tareas para cada usuario simulado
    wait_time = between(1, 3)

    @task
    def login(self):
        """
        Tarea que simula una petición de login.
        """
        try:
            # Datos para el login
            payload = {
                "username": "admin",
                "password": "admin123",
                "company_slug": "fastops"
            }
            
            # Realizar la petición POST al endpoint de login
            self.client.post("/auth/login", json=payload)

        except Exception as e:
            # En caso de error, puedes registrarlo si es necesario
            # print(f"Ocurrió un error durante el login: {e}")
            pass

    def on_start(self):
        """
        Código que se ejecuta cuando un usuario simulado (locust) inicia.
        En este caso no es necesario, pero es útil para logins complejos
        donde se necesita un token para las demás tareas.
        """
        pass
