export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Open Clinic AI
        </h1>
        <p className="text-gray-600 mb-8">
          Sistema open-source de gestão para clínicas
        </p>
        <a
          href="/admin"
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors mr-4"
        >
          Painel Admin
        </a>
        <a
          href="/secretary"
          className="inline-block bg-gray-100 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Secretária
        </a>
      </div>
    </main>
  );
}
