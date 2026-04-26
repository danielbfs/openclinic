"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface ScheduleRow {
  day_of_week: number;
  start_time: string; // "HH:MM:SS" from backend
  end_time: string;
}

const DAY_NAMES = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

function toHHMM(t: string) {
  return t.slice(0, 5); // "08:00:00" → "08:00"
}

export default function DoctorSchedulePage() {
  const { user } = useAuth();
  const [rows, setRows] = useState<ScheduleRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!user?.doctor_id) return;
    api
      .get(`/scheduling/doctors/${user.doctor_id}/schedule`)
      .then(({ data }) => setRows(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user?.doctor_id]);

  function addRow() {
    setRows([...rows, { day_of_week: 0, start_time: "08:00", end_time: "12:00" }]);
  }

  function removeRow(idx: number) {
    setRows(rows.filter((_, i) => i !== idx));
  }

  function updateRow(idx: number, field: keyof ScheduleRow, value: string | number) {
    setRows(rows.map((r, i) => (i === idx ? { ...r, [field]: value } : r)));
  }

  async function save() {
    if (!user?.doctor_id) return;
    setSaving(true);
    try {
      await api.put(`/scheduling/doctors/${user.doctor_id}/schedule`, {
        schedules: rows.map((r) => ({
          day_of_week: Number(r.day_of_week),
          start_time: toHHMM(r.start_time),
          end_time: toHHMM(r.end_time),
        })),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      alert("Erro ao salvar horários.");
    } finally {
      setSaving(false);
    }
  }

  if (!user?.doctor_id) {
    return (
      <main className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-yellow-800">
          Seu usuário não está vinculado a nenhum médico. Contate o administrador.
        </div>
      </main>
    );
  }

  return (
    <main className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Meus Horários</h1>
      <p className="text-sm text-gray-500 mb-6">
        Configure os dias e horários em que você está disponível para consultas.
      </p>

      {saved && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-700 text-sm px-4 py-2 rounded-lg">
          Horários salvos com sucesso.
        </div>
      )}

      {loading ? (
        <p className="text-gray-400">Carregando...</p>
      ) : (
        <div className="bg-white border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left p-3 font-medium text-gray-600">Dia</th>
                <th className="text-left p-3 font-medium text-gray-600">Início</th>
                <th className="text-left p-3 font-medium text-gray-600">Fim</th>
                <th className="p-3" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {rows.length === 0 && (
                <tr>
                  <td colSpan={4} className="p-6 text-center text-gray-400">
                    Nenhum horário configurado.
                  </td>
                </tr>
              )}
              {rows.map((row, idx) => (
                <tr key={idx}>
                  <td className="p-3">
                    <select
                      value={row.day_of_week}
                      onChange={(e) => updateRow(idx, "day_of_week", Number(e.target.value))}
                      className="border rounded-lg px-2 py-1.5 text-sm w-full"
                    >
                      {DAY_NAMES.map((name, d) => (
                        <option key={d} value={d}>{name}</option>
                      ))}
                    </select>
                  </td>
                  <td className="p-3">
                    <input
                      type="time"
                      value={toHHMM(row.start_time)}
                      onChange={(e) => updateRow(idx, "start_time", e.target.value)}
                      className="border rounded-lg px-2 py-1.5 text-sm w-full"
                    />
                  </td>
                  <td className="p-3">
                    <input
                      type="time"
                      value={toHHMM(row.end_time)}
                      onChange={(e) => updateRow(idx, "end_time", e.target.value)}
                      className="border rounded-lg px-2 py-1.5 text-sm w-full"
                    />
                  </td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => removeRow(idx)}
                      className="text-red-400 hover:text-red-600 text-xs px-2 py-1 rounded"
                    >
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="p-3 border-t flex items-center justify-between">
            <button
              onClick={addRow}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              + Adicionar horário
            </button>
            <button
              onClick={save}
              disabled={saving}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "Salvando..." : "Salvar Horários"}
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
