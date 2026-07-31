import { ShieldOff } from "lucide-react";
import { Link } from "react-router-dom";

export default function ForbiddenPage() {
  return (
    <main className="flex min-h-full items-center justify-center bg-gray-50 p-6">
      <div className="max-w-md space-y-3 rounded-2xl bg-white p-8 text-center shadow-sm">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600"><ShieldOff size={22} /></span>
        <h1 className="text-xl font-bold text-gray-900">Ruxsat yo'q</h1>
        <p className="text-sm text-gray-500">Bu bo'lim sizning rolingiz uchun ochiq emas. Kerak bo'lsa administratorga murojaat qiling.</p>
        <Link to="/" className="inline-flex rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700">Boshqaruv paneliga qaytish</Link>
      </div>
    </main>
  );
}
