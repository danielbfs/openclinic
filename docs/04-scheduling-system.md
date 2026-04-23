---
tags: [openclinic, scheduling]
created: 2026-04-23
status: draft
---

# Sistema de Agendamento — Open Clinic AI

## Visão Geral

O `SchedulingService` é uma camada de abstração que oferece interface unificada para agendamento, independentemente do provider configurado por médico.

Cada médico tem:
- `scheduling_provider`: `google_calendar` ou `local_db`
- `provider_config`: JSON com configurações específicas do provider
- `slot_duration_minutes`: duração padrão de cada consulta

---

## Interface Abstrata

```python
class AbstractSchedulingAdapter:
    async def get_availability(self, date_from, date_to) -> list[TimeRange]: ...
    async def get_booked_slots(self, date_from, date_to) -> list[TimeRange]: ...
    async def create_event(self, patient_id, starts_at, ends_at, notes) -> ExternalEvent: ...
    async def cancel_event(self, external_event_id) -> None: ...
    async def reschedule_event(self, external_event_id, new_starts_at, new_ends_at) -> None: ...
```

---

## Algoritmo de Disponibilidade

```
Entrada: doctor_id, date_from, date_to, slot_duration (minutos)

1. Busca regras recorrentes (doctor_schedules)
   → Expande para lista de janelas no período: [(seg 09:00, seg 18:00), ...]

2. Gera todos os slots possíveis dentro das janelas
   → Intervalo de slot_duration_minutes: 09:00, 09:30, 10:00 ...

3. Remove bloqueios (schedule_blocks) que sobrepõem ao slot

4. Remove agendamentos existentes com status != 'cancelled'
   → Busca no DB (local_db) ou via freebusy API (Google Calendar)

5. Remove slots no passado

6. Retorna: list[TimeSlot{starts_at, ends_at, is_available: True}]
```

---

## Prevenção de Conflitos

### Nível Banco de Dados
```sql
-- Constraint EXCLUDE previne overlap em nível de DB
CONSTRAINT no_overlap EXCLUDE USING gist (
    doctor_id WITH =,
    tstzrange(starts_at, ends_at) WITH &&
) WHERE (status NOT IN ('cancelled'))
```

### Nível Aplicação (Race Condition)
```python
async def book_appointment(self, doctor_id, starts_at, ends_at, ...):
    async with db.begin():
        # SELECT FOR UPDATE — bloqueia a linha durante a transação
        existing = await db.execute(
            select(Appointment)
            .where(Appointment.doctor_id == doctor_id)
            .where(Appointment.starts_at < ends_at)
            .where(Appointment.ends_at > starts_at)
            .where(Appointment.status != 'cancelled')
            .with_for_update()
        )
        if existing.scalar():
            raise SlotNotAvailableError("Horário já ocupado")
        # Cria o agendamento
        ...
```

### Cache de Slots (Redis)
- Slot exibido para o paciente: reservado em cache Redis por 5 minutos
- Chave: `slot_lock:{doctor_id}:{starts_at_iso}`
- Se expirado antes da confirmação: slot liberado automaticamente

---

## Google Calendar Adapter

### Fluxo OAuth
```
Admin acessa /admin/google/oauth
  → Redirect para Google OAuth consent screen
  → Callback em /admin/google/callback?code=...
    → Troca code por access_token + refresh_token
    → Salva criptografado no DB (key: env ENCRYPTION_KEY)
    → Associa credentials ao doctor.provider_config
```

### Leitura de Disponibilidade
```python
# Mais eficiente que listar todos os eventos
response = calendar_service.freebusy().query({
    "timeMin": date_from.isoformat(),
    "timeMax": date_to.isoformat(),
    "items": [{"id": doctor.provider_config["calendar_id"]}]
}).execute()

busy_slots = response["calendars"][calendar_id]["busy"]
# [{start: "...", end: "..."}, ...]
```

### Criação de Evento
```python
event = {
    "summary": f"Consulta — {patient.full_name}",
    "start": {"dateTime": starts_at.isoformat(), "timeZone": CLINIC_TIMEZONE},
    "end":   {"dateTime": ends_at.isoformat(),   "timeZone": CLINIC_TIMEZONE},
    "colorId": "2",  # cor padrão para eventos Open Clinic
    "extendedProperties": {
        "private": {
            "openclinic_appointment_id": str(appointment_id),
            "openclinic_patient_phone": patient.phone
        }
    }
}
```

---

## Local DB Adapter

### Leitura de Disponibilidade
```python
# Busca diretamente nas tabelas doctor_schedules e appointments
schedules = await db.execute(
    select(DoctorSchedule)
    .where(DoctorSchedule.doctor_id == doctor_id)
    .where(DoctorSchedule.is_active == True)
)

booked = await db.execute(
    select(Appointment)
    .where(Appointment.doctor_id == doctor_id)
    .where(Appointment.starts_at >= date_from)
    .where(Appointment.ends_at <= date_to)
    .where(Appointment.status != 'cancelled')
)
```

---

## Endpoints

```
GET /api/v1/scheduling/slots
  Params: doctor_id | specialty_id, date_from, date_to
  Returns: list[{starts_at, ends_at, doctor_id, doctor_name}]

GET /api/v1/scheduling/calendar
  Params: date_from, date_to
  Returns: visão consolidada de todos os médicos

POST /api/v1/scheduling/blocks
  Body: {doctor_id, starts_at, ends_at, reason}

DELETE /api/v1/scheduling/blocks/{id}
```
