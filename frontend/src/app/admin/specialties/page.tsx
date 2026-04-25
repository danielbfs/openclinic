"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Specialty } from "@/types";

export default function SpecialtiesPage() {
  const [specialties, setSpecialties] = useState<Specialty[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", description: "" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSpecialties();
  }, []);

  async function fetchSpecialties() {
    try {
      const { data } = await api.get("/specialties/");
      setSpecialties(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setEditingId(null);
    setForm({ name: "", description: "" });
    setShowForm(true);
  }

  function openEdit(spec: Specialty) {
    setEditingId(spec.id);
    setForm({ name: spec.name, description: spec.description || "" });
    setShowForm(true);
  }

  function cancelForm() {
    setShowForm(false);
    setEditingId(null);
    setForm({ name: "", description: "" });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      if (editingId) {
        await api.patch(`/specialties/${editingId}`, {
          name: form.name,
          description: form.description || null,
        });
      } else {
        await api.post("/specialties/", {
          name: form.name,
          description: form.description || null,
        });
      }
      cancelForm();
      fetchSpecialties();
    } catch {
      alert("Erro ao salvar especialidade.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(spec: Specialty) {
    try {
      await api.patch(`/specialties/${spec.id}`, { is_active: !spec.is_active });
      fetchSpecialties();
    } catch {
      // ignore
    }
  }

  async function handleDelete(spec: Specialty) {
    if (!confirm(`Deseja excluir a especialidade "${spec.name}"?`)) return;
    try {
      await api.delete(`/specialties/${spec.id}`);
      fetchSpecialties();
    } catch {
      alert("Erro ao excluir. Pode haver médicos vinculados.");
    }
  }

  if (loading) return <div className="p-8 text-gray-400">Carregando...</div>;

  return (
    <main className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Especialidades</h1>
        <button
          onClick={showForm ? cancelForm : openCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          {showForm ? "Cancelar" : "Nova Especialidade"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white border rounded-lg p-4 mb-6 space-y-3">
          <h3 className="text-sm font-semibold text-gray-700">
            {editingId ? "Editar Especialidade" : "Nova Especialidade"}
          </h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
              className="w-full border rounded-lg px-3 py-2 text-sm"
              placeholder="Ex: Cardiologia"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
            <input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm"
              placeholder="Opcional"
            />
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

      <div className="bg-white border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Nome</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Descrição</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Status</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {specialties.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                  Nenhuma especialidade cadastrada.
                </td>
              </tr>
            ) : (
              specialties.map((spec) => (
                <tr key={spec.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{spec.name}</td>
                  <td className="px-4 py-3 text-gray-500">{spec.description || "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        spec.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {spec.is_active ? "Ativa" : "Inativa"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-3">
                      <button onClick={() => openEdit(spec)} className="text-xs text-blue-600 hover:underline">
                        Editar
                      </button>
                      <button onClick={() => toggleActive(spec)} className="text-xs text-yellow-600 hover:underline">
                        {spec.is_active ? "Desativar" : "Ativar"}
                      </button>
                      <button onClick={() => handleDelete(spec)} className="text-xs text-red-600 hover:underline">
                        Excluir
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
