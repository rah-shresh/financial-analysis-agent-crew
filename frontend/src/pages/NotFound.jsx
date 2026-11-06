import { Link } from "react-router-dom";
 
export default function NotFound() {
  return (
    <div className="mx-auto max-w-md px-5 py-24 text-center">
      <p className="num text-5xl text-stamp">404</p>
      <h1 className="mt-3 text-xl font-semibold">Page not found</h1>
      <Link to="/" className="btn-ghost mt-6 inline-block">Back to the dashboard</Link>
    </div>
  );
}
