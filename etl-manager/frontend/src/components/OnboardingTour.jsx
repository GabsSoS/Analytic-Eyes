import { useEffect, useState, useLayoutEffect } from "react";
import { useTour } from "../context/TourContext";
import "./OnboardingTour.css";

const PADDING = 8;

function useTargetRect(selector) {
  const [rect, setRect] = useState(null);

  useLayoutEffect(() => {
    if (!selector) {
      setRect(null);
      return;
    }

    const el = document.querySelector(selector);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });

    const update = () => {
      const target = document.querySelector(selector);
      setRect(target ? target.getBoundingClientRect() : null);
    };

    update();
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    const raf = requestAnimationFrame(update);

    return () => {
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
      cancelAnimationFrame(raf);
    };
  }, [selector]);

  return rect;
}

function OnboardingTour() {
  const { isActive, step, stepIndex, totalSteps, nextStep, prevStep, skipTour } = useTour();
  const rect = useTargetRect(step?.target);

  useEffect(() => {
    if (!isActive) return;
    const onKeyDown = (e) => {
      if (e.key === "Escape") skipTour();
      if (e.key === "ArrowRight") nextStep();
      if (e.key === "ArrowLeft") prevStep();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [isActive, nextStep, prevStep, skipTour]);

  if (!isActive || !step) return null;

  const isCentered = !step.target || !rect;

  let tooltipStyle = {};
  let arrowClass = "";

  if (!isCentered) {
    const spaceBelow = window.innerHeight - rect.bottom;
    const placeBelow = spaceBelow > 200;
    const top = placeBelow ? rect.bottom + 14 : rect.top - 14;
    const left = Math.min(
      Math.max(rect.left + rect.width / 2, 190),
      window.innerWidth - 190
    );
    tooltipStyle = {
      top: placeBelow ? top : undefined,
      bottom: placeBelow ? undefined : window.innerHeight - top,
      left,
      transform: "translateX(-50%)",
    };
    arrowClass = placeBelow ? "tour-arrow-up" : "tour-arrow-down";
  }

  return (
    <div className="tour-overlay" role="dialog" aria-modal="true" aria-label="Tour guiado">
      {!isCentered && (
        <div
          className="tour-spotlight"
          style={{
            top: rect.top - PADDING,
            left: rect.left - PADDING,
            width: rect.width + PADDING * 2,
            height: rect.height + PADDING * 2,
          }}
        />
      )}
      {isCentered && <div className="tour-backdrop" />}

      <div
        className={`tour-tooltip ${isCentered ? "tour-tooltip-centered" : arrowClass}`}
        style={isCentered ? {} : tooltipStyle}
      >
        <button type="button" className="tour-close" aria-label="Fechar tour" onClick={skipTour}>
          ×
        </button>
        <span className="tour-step-count">{stepIndex + 1} de {totalSteps}</span>
        <h3>{step.title}</h3>
        <p>{step.body}</p>
        <div className="tour-progress">
          {Array.from({ length: totalSteps }).map((_, i) => (
            <span key={i} className={`tour-dot ${i === stepIndex ? "active" : ""} ${i < stepIndex ? "done" : ""}`} />
          ))}
        </div>
        <div className="tour-actions">
          <button type="button" className="tour-btn ghost" onClick={skipTour}>
            Pular tour
          </button>
          <div className="tour-actions-nav">
            {stepIndex > 0 && (
              <button type="button" className="tour-btn secondary" onClick={prevStep}>
                Voltar
              </button>
            )}
            <button type="button" className="tour-btn primary" onClick={nextStep}>
              {stepIndex + 1 === totalSteps ? "Concluir" : "Próximo"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OnboardingTour;
