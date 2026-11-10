from abc import ABC, abstractmethod


# Interface base do Observer
class ObservadorRisco(ABC):

    @abstractmethod
    def atualizar(self, cidade: str, alerta: str, nivel_risco: str):
        pass


# Observer concreto: simula a notificação à Defesa Civil
class DefesaCivilNotifier(ObservadorRisco):

    def atualizar(self, cidade: str, alerta: str, nivel_risco: str):

        if nivel_risco == "CRITICO":
            print(f"\n🚨 [DEFESA CIVIL NOTIFICADA] Equipes despachadas para {cidade}!")
            print(f"   Motivo: Risco CRÍTICO de {alerta}.")


# Observer concreto: registra eventos severos
class LogAuditoria(ObservadorRisco):

    def atualizar(self, cidade: str, alerta: str, nivel_risco: str):

        if nivel_risco in ["ALTO", "CRITICO"]:

            nivel_exibido = "CRÍTICO" if nivel_risco == "CRITICO" else nivel_risco

            print(
                f"📝 [LOG AUDITORIA] Evento severo registrado em "
                f"{cidade}: {alerta} ({nivel_exibido})"
            )


# Subject: central responsável por gerenciar os observadores
class CentralNotificacoes:

    def __init__(self):
        self._inscritos = []

    def inscrever(self, observador: ObservadorRisco):
        if observador not in self._inscritos:
            self._inscritos.append(observador)

    def cancelar(self, observador: ObservadorRisco):
        if observador in self._inscritos:
            self._inscritos.remove(observador)

    def notificar_todos(self, cidade: str, alerta: str, nivel_risco: str):
        for observador in self._inscritos:
            observador.atualizar(cidade, alerta, nivel_risco)