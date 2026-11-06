import SentimentGauge from "../../components/SentimentGauge";
import { SectionHead, Unavailable } from "../../components/ui";
import { splitHeadline } from "../../services/format";
 
export default function SentimentTab({ report }) {
  const s = report.sentiment;
  if (!s) return <Unavailable what="News sentiment" reason={report.errors?.sentiment} />;
 
  return (
    <div className="space-y-8">
      <section className="max-w-xl">
        <SectionHead number="01">Score across {s.headlines.length} recent headlines</SectionHead>
        <SentimentGauge score={s.score} label={s.label} />
        <p className="mt-4 text-sm text-ink-soft">
          Scored with a simple word-based model. It reads everyday opinion words well but often misses financial
          wording (“beats estimates”, “jumps 5%”), so headlines that read as clearly positive to a person can still
          score near zero. Treat it as a rough signal.
        </p>
      </section>
 
      <section>
        <SectionHead number="02">Headlines read</SectionHead>
        <ul className="divide-y divide-rule-soft border-y border-rule-soft">
          {s.headlines.map((h, i) => {
            const { title, source } = splitHeadline(h);
            return (
              <li key={i} className="flex items-baseline gap-3 px-1 py-2.5 text-sm">
                <span className="num w-5 text-xs text-ink-soft">{i + 1}</span>
                <span className="flex-1">{title}</span>
                {source && <span className="shrink-0 text-xs italic text-ink-soft">{source}</span>}
              </li>
            );
          })}
        </ul>
      </section>
    </div>
  );
}
 












