"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Doctor, Specialty } from "@/types";

const DAYS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

interface ScheduleItem {
  day_of_week: number;
  start_time: string;
  end_time: string;
}

export default function DoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [specialties, setSpecialties] = useState<Specialty[]>([]);
  const [loading, setLoading] = useState(true);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({
    full_name: "",
    crm: "",
    specialty_id: "",
    slot_duration_minutes: 30,
  });
  const [saving, setSaving] = useState(false);

  // Schedule modal
  const [scheduleDoctor, setScheduleDoctor] = useState<Doctor | null>(null);
  const [scheduleItems, setScheduleItems] = useState<ScheduleItem[]>([]);
  const [savingSchedule, setSavingSchedule] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      const [docsRes, specsRes] = await Promise.allSettled([
        api.get("/scheduling/doctors"),
        api.get("/specialties/"),
      ]);
      if (docsRes.status === "fulfilled") setDoctors(docsRes.value.data);
      if (specsRes.status === "fulfilled") setSpecialties(specsRes.value.data);
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setEditingId(null);
    setForm({ full_name: "", crm: "", specialty_id: "", slot_duration_minutes: 30 });
    setShowForm(true);
  }

  function openEdit(doc: Doctor) {
    setEditingId(doc.id);
    setForm({
      full_name: doc.full_name,
      crm: doc.crm || "",
      specialty_id: doc.specialty_id || "",
      slot_duration_minutes: doc.slot_duration_minutes,
    });
    setShowForm(true);
  }

  function cancelForm() {
    setShowForm(false);
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        full_name: form.full_name,
        crm: form.crm || null,
        specialty_id: form.specialty_id || null,
        slot_duration_minutes: form.slot_duration_minutes,
      };
      if (editingId) {
        await api.patch(`/scheduling/doctors/${editingId}`, payload);
      } else {
        await api.post("/scheduling/doctors", payload);
      }
      cancelForm();
      fetchData();
    } catch {
      alert("Erro ao salvar médico.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(doc: Doctor) {
    try {
      await api.patch(`/scheduling/doctors/${doc.id}`, { is_active: !doc.is_active });
      fetchData();
    } catch {
      // ignore
    }
  }

  async function openSchedule(doc: Doctor) {
    setScheduleDoctor(doc);
    try {
      const { data } = await api.get(`/scheduling/doctors/${doc.id}/schedule`);
      setScheduleItems(
        data.map((s: { day_of_week: number; start_time: string; end_time: string }) => ({
          day_of_week: s.day_of_week,
          start_time: s.start_time.slice(0, 5),
          end_time: s.end_time.slice(0, 5),
        }))
      );
    } catch {
      setScheduleItems([]);
    }
  }

  function addScheduleRow() {
    setScheduleItems([...scheduleItems, { day_of_week: 0, start_time: "08:00", end_time: "12:00" }]);
  }

  function removeScheduleRow(idx: number) {
    setScheduleItems(scheduleItems.filter((_, i) => i !== idx));
  }

  function updateScheduleRow(idx: number, field: keyof ScheduleItem, value: string | number) {
    const updated = [...scheduleItems];
    if (field === "day_of_week") {
      updated[idx] = { ...updated[idx], day_of_week: value as number };
    } else {
      updated[idx] = { ...updated[idx], [field]: value as string };
    }
    setScheduleItems(updated);
  }

  async function saveSchedule() {
    if (!scheduleDoctor) return;
    setSavingSchedule(true);
    try {
      await api.put(`/scheduling/doctors/${scheduleDoctor.id}/schedule`, {
        schedules: scheduleItems,
      });
      setScheduleDoctor(null);
    } catch {
      alert("Erro ao salvar horários.");
    } finally {
      setSavingSchedule(false);
    }
  }

  const specName = (id: string | null) => (id ? specialties.find((s) => s.id === id)?.name : null) || "—";

  if (loading) return <div className="p-8 text-gray-400">Carregando...</div>;

  return (
    <main className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Médicos</h1>
        <button
          onClick={showForm ? cancelForm : openCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          {showForm ? "Cancelar" : "Novo Médico"}
        </button>
      </div>

      {/* Create/Edit Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white border rounded-lg p-4 mb-6 space-y-3">
          <h3 className="text-sm font-semibold text-gray-700">
            {editingId ? "Editar Médico" : "Novo Médico"}
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome completo</label>
              <input
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                required
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">CRM</label>
              <input
                value={form.crm}
                onChange={(e) => setForm({ ...form, crm: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="Opcional"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Especialidade</label>
              <select
                value={form.specialty_id}
                onChange={(e) => setForm({ ...form, specialty_id: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                <option value="">Sem especialidade</option>
                {specialties.filter((s) => s.is_active).map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Duração do slot (min)</label>
              <input
                type="number"
                value={form.slot_duration_minutes}
                onChange={(e) => setForm({ ...form, slot_duration_minutes: Number(e.target.value) })}
                min={10}
                max={120}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "Salvando..." : editingId ? "Salvar" : "Criar"}
            </button>
            <button type="button" onClick={cancelForm} className="text-sm text-gray-500 px-4 py-2">
              Cancelar
            </button>
          </div>
        </form>
      )}

      {/* Schedule Modal */}
      {scheduleDoctor && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-gray-900 mb-1">
              Horários — {scheduleDoctor.full_name}
            </h2>
            <p className="text-sm text-gray-500 mb-4">Configure os horários de atendimento recorrentes.</p>

            {scheduleItems.length === 0 ? (
              <p className="text-sm text-gray-400 mb-4">Nenhum horário cadastrado.</p>
            ) : (
              <div className="space-y-2 mb-4">
                {scheduleItems.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <select
                      value={item.day_of_week}
                      onChange={(e) => updateScheduleRow(idx, "day_of_week", Number(e.target.value))}
                      className="border rounded px-2 py-1.5 text-sm flex-1"
                    >
                      {DAYS.map((d, i) => (
                        <option key={i} value={i}>{d}</option>
                      ))}
                    </select>
                    <input
                      type="time"
                      value={item.start_time}
                      onChange={(e) => updateScheduleRow(idx, "start_time", e.target.value)}
                      className="border rounded px-2 py-1.5 text-sm"
                    />
                    <span className="text-gray-400">—</span>
                    <input
                      type="time"
                      value={item.end_time}
                      onChange={(e) => updateScheduleRow(idx, "end_time", e.target.value)}
                      className="border rounded px-2 py-1.5 text-sm"
                    />
                    <button
                      onClick={() => removeScheduleRow(idx)}
                      className="text-red-500 hover:text-red-700 text-sm px-1"
                    >
                      X
                    </button>
                  </div>
                ))}
              </div>
            )}

            <button onClick={addScheduleRow} className="text-sm text-blue-600 hover:underline mb-4 block">
              + Adicionar horário
            </button>

            <div className="flex gap-2 justify-end border-t pt-4">
              <button
                onClick={() => setScheduleDoctor(null)}
                className="text-sm text-gray-500 px-4 py-2"
              >
                Cancelar
              </button>
              <button
                onClick={saveSchedule}
                disabled={savingSchedule}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {savingSchedule ? "Salvando..." : "Salvar Horários"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Doctors Table */}
      <div className="bg-white border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Nome</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">CRM</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Especialidade</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Slot</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Status</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {doctors.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  Nenhum médico cadastrado.
                </td>
              </tr>
            ) : (
              doctors.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{doc.full_name}</td>
                  <td className="px-4 py-3 text-gray-500">{doc.crm || "—"}</td>
                  <td className="px-4 py-3 text-gray-500">{specName(doc.specialty_id)}</td>
                  <td className="px-4 py-3 text-gray-500">{doc.slot_duration_minutes} min</td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        doc.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {doc.is_active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-3">
                      <button onClick={() => openEdit(doc)} className="text-xs text-blue-600 hover:underline">
                        Editar
                      </button>
                      <button onClick={() => openSchedule(doc)} className="text-xs text-purple-600 hover:underline">
                        Horários
                      </button>
                      <button onClick={() => toggleActive(doc)} className="text-xs text-yellow-600 hover:underline">
                        {doc.is_active ? "Desativar" : "Ativar"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}
