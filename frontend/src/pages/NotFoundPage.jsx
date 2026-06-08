import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <main className="not-found-page">
      <section className="login-card">
        <p className="eyebrow">404</p>
        <h1>Страница не найдена</h1>
        <p>Проверьте адрес или вернитесь на рабочую панель.</p>
        <Link className="button-link" to="/dashboard">
          На панель
        </Link>
      </section>
    </main>
  );
}
