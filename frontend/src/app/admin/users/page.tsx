"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Doctor, User } from "@/types";

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrador",
  secretary: "Secretária",
  doctor: "Médico",
};

const ROLE_COLORS: Record<string, string> = {
  admin: "bg-purple-100 text-purple-700",
  secretary: "bg-blue-100 text-blue-700",
  doctor: "bg-teal-100 text-teal-700",
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({
    username: "",
    full_name: "",
    password: "",
    role: "secretary" as string,
    doctor_id: "" as string,
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchUsers();
    api.get("/scheduling/doctors?active_only=false").then(({ data }) => setDoctors(data)).catch(() => {});
  }, []);

  async function fetchUsers() {
    try {
      const { data } = await api.get("/auth/users");
      setUsers(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setEditingId(null);
    setForm({ username: "", full_name: "", password: "", role: "secretary", doctor_id: "" });
    setShowForm(true);
  }

  function openEdit(user: User) {
    setEditingId(user.id);
    setForm({
      username: user.username,
      full_name: user.full_name,
      password: "",
      role: user.role,
      doctor_id: user.doctor_id || "",
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
      const doctor_id = form.role === "doctor" && form.doctor_id ? form.doctor_id : null;

      if (editingId) {
        const payload: Record<string, unknown> = {
          username: form.username,
          full_name: form.full_name,
          role: form.role,
          doctor_id,
        };
        await api.patch(`/auth/users/${editingId}`, payload);
      } else {
        if (!form.password) { alert("Senha é obrigatória para novo usuário."); setSaving(false); return; }
        await api.post("/auth/users", {
          username: form.username,
          full_name: form.full_name,
          password: form.password,
          role: form.role,
          doctor_id,
        });
      }
      cancelForm();
      fetchUsers();
    } catch {
      alert("Erro ao salvar usuário.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(user: User) {
    try { await api.patch(`/auth/users/${user.id}`, { is_active: !user.is_active }); fetchUsers(); }
    catch { /* ignore */ }
  }

  async function resetPassword(user: User) {
    if (!confirm(`Resetar a senha de "${user.full_name}" para o padrão?`)) return;
    try {
      const { data } = await api.post(`/auth/users/${user.id}/reset-password`);
      alert(data.message);
    } catch { alert("Erro ao resetar senha."); }
  }

  function doctorName(doctorId: string | null) {
    if (!doctorId) return null;
    return doctors.find((d) => d.id === doctorId)?.full_name || null;
  }

  if (loading) return <div className="p-8 text-gray-400">Carregando...</div>;

  return (
    <main className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Usuários do Sistema</h1>
        <button
          onClick={showForm ? cancelForm : openCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          {showForm ? "Cancelar" : "Novo Usuário"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white border rounded-lg p-4 mb-6 space-y-3">
          <h3 className="text-sm font-semibold text-gray-700">
            {editingId ? "Editar Usuário" : "Novo Usuário"}
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Login (username)</label>
              <input
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                required
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Nome completo</label>
              <input
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                required
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            {!editingId && (
              <div>
                <label className="block text-xs text-gray-500 mb-1">Senha</label>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required={!editingId}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder="Mín. 6 caracteres"
                />
              </div>
            )}
            <div>
              <label className="block text-xs text-gray-500 mb-1">Perfil</label>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value, doctor_id: "" })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                <option value="admin">Administrador</option>
                <option value="secretary">Secretária</option>
                <option value="doctor">Médico</option>
              </select>
            </div>
            {form.role === "doctor" && (
              <div className="col-span-2">
                <label className="block text-xs text-gray-500 mb-1">Médico vinculado</label>
                <select
                  value={form.doctor_id}
                  onChange={(e) => setForm({ ...form, doctor_id: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">— Nenhum —</option>
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.full_name}{d.crm ? ` (${d.crm})` : ""}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  Vincule a um médico para dar acesso ao portal do médico.
                </p>
              </div>
            )}
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
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Login</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Nome</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Perfil</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Médico</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Status</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{user.username}</td>
                <td className="px-4 py-3 text-gray-600">{user.full_name}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ROLE_COLORS[user.role] || "bg-gray-100 text-gray-600"}`}>
                    {ROLE_LABELS[user.role] || user.role}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {doctorName(user.doctor_id) || "—"}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${user.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                    {user.is_active ? "Ativo" : "Inativo"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-3">
                    <button onClick={() => openEdit(user)} className="text-xs text-blue-600 hover:underline">Editar</button>
                    <button onClick={() => resetPassword(user)} className="text-xs text-orange-600 hover:underline">Reset Senha</button>
                    <button onClick={() => toggleActive(user)} className="text-xs text-yellow-600 hover:underline">
                      {user.is_active ? "Desativar" : "Ativar"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
