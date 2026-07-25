import { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useLocation } from "react-router-dom";

const STORAGE_PREFIX = "onboardingTourSeen";

// Cada flow é um tour independente, ligado a uma rota, com seu próprio
// progresso salvo no localStorage. "target" é o seletor CSS do elemento a
// destacar (via data-tour=... nos componentes); null = passo central, sem
// destaque (boas-vindas/encerramento).
const TOUR_FLOWS = {
  home: {
    storageKey: STORAGE_PREFIX,
    matches: (pathname) => pathname === "/home",
    steps: [
      {
        id: "welcome",
        target: null,
        title: "Bem-vindo(a) ao Analytic Eyes! 👋",
        body: "Vamos fazer um tour rápido pelas principais áreas do sistema — leva menos de um minuto.",
      },
      {
        id: "nav-home",
        target: '[data-tour="nav-home"]',
        title: "Início",
        body: "Seu painel: quantos fluxos você tem, quantos são seus, compartilhados, e o status das últimas execuções.",
      },
      {
        id: "nav-criar",
        target: '[data-tour="nav-criar"]',
        title: "Criar Fluxo",
        body: "Crie uma nova pipeline: escreva ou envie o código Python, defina as dependências e, se quiser, um agendamento recorrente.",
      },
      {
        id: "nav-fluxos",
        target: '[data-tour="nav-fluxos"]',
        title: "Fluxos",
        body: "Veja todos os fluxos que você criou ou que outras pessoas compartilharam com você, com busca e acesso rápido aos detalhes.",
      },
      {
        id: "nav-settings",
        target: '[data-tour="nav-settings"]',
        title: "Configurações",
        body: "Altere sua senha e, se você for administrador, gerencie outras contas (criar, promover, desativar, redefinir senha).",
      },
      {
        id: "header-search",
        target: '[data-tour="header-search"]',
        title: "Busca rápida",
        body: "Digite aqui para encontrar um fluxo pelo nome ou pular direto para qualquer tela do sistema.",
      },
      {
        id: "header-help",
        target: '[data-tour="header-help"]',
        title: "Precisa rever isso depois?",
        body: "Clique neste ícone a qualquer momento para refazer o tour da tela em que você está.",
      },
    ],
  },
  criar: {
    storageKey: `${STORAGE_PREFIX}:criar`,
    matches: (pathname) => pathname.startsWith("/criar") || pathname.startsWith("/editar"),
    steps: [
      {
        id: "criar-welcome",
        target: null,
        title: "Como criar um fluxo",
        body: "Vamos ver rapidamente cada parte do formulário de criação de um novo fluxo.",
      },
      {
        id: "criar-geral",
        target: '[data-tour="criar-geral"]',
        title: "Informações gerais",
        body: "Dê um nome e uma descrição ao fluxo e, se quiser, já adicione colaboradores.",
      },
      {
        id: "criar-script",
        target: '[data-tour="criar-script"]',
        title: "Script da pipeline",
        body: "Envie um arquivo .py ou escreva o código diretamente no editor.",
      },
      {
        id: "criar-config",
        target: '[data-tour="criar-config"]',
        title: "Arquivo de configuração",
        body: "Opcionalmente, envie um .env ou .ini com variáveis usadas pelo script.",
      },
      {
        id: "criar-libs",
        target: '[data-tour="criar-libs"]',
        title: "Bibliotecas",
        body: "Liste as dependências Python que o script precisa para rodar.",
      },
      {
        id: "criar-submit",
        target: '[data-tour="criar-submit"]',
        title: "Criar fluxo",
        body: "Quando terminar, clique aqui para salvar. Depois, na tela de detalhes do fluxo, você pode agendar, ancorar e compartilhar com outras pessoas.",
      },
    ],
  },
  details: {
    storageKey: `${STORAGE_PREFIX}:details`,
    matches: (pathname) => pathname.startsWith("/Details"),
    steps: [
      {
        id: "details-welcome",
        target: null,
        title: "Detalhes do fluxo",
        body: "Aqui você acompanha execuções e configura agendamento, ancoragem e compartilhamento deste fluxo.",
      },
      {
        id: "details-agendamento",
        target: '[data-tour="details-agendamento"]',
        title: "Agendamento",
        body: "Veja se o fluxo roda automaticamente e em quais dias e horários.",
      },
      {
        id: "details-ancoragem",
        target: '[data-tour="details-ancoragem"]',
        title: "Ancoragem",
        body: "Encadeie fluxos: defina que este fluxo rode automaticamente após o sucesso de outro.",
      },
      {
        id: "details-colaboradores",
        target: '[data-tour="details-colaboradores"]',
        title: "Compartilhamento",
        body: "Veja quem tem acesso a este fluxo e qual o nível de permissão de cada colaborador.",
      },
      {
        id: "details-editar",
        target: '[data-tour="details-editar"]',
        title: "Editar tudo aqui",
        body: "Clique em Editar para alterar agendamento, ancoragem e colaboradores.",
      },
    ],
  },
};

const AUTO_START_DELAY_MS = 700;

const TourContext = createContext(null);

export function TourProvider({ children }) {
  const location = useLocation();
  const [activeFlowId, setActiveFlowId] = useState(null);
  const [stepIndex, setStepIndex] = useState(-1);

  const activeFlow = activeFlowId ? TOUR_FLOWS[activeFlowId] : null;
  const isActive = activeFlow !== null && stepIndex >= 0;

  const flowForPath = useCallback((pathname) => {
    const entry = Object.entries(TOUR_FLOWS).find(([, flow]) => flow.matches(pathname));
    return entry ? { id: entry[0], flow: entry[1] } : null;
  }, []);

  useEffect(() => {
    if (activeFlowId) return;
    const match = flowForPath(location.pathname);
    if (!match) return;
    if (localStorage.getItem(match.flow.storageKey)) return;

    const timer = setTimeout(() => {
      setActiveFlowId(match.id);
      setStepIndex(0);
    }, AUTO_START_DELAY_MS);
    return () => clearTimeout(timer);
  }, [location.pathname, activeFlowId, flowForPath]);

  const finishTour = useCallback(() => {
    if (activeFlow) localStorage.setItem(activeFlow.storageKey, "true");
    setStepIndex(-1);
    setActiveFlowId(null);
  }, [activeFlow]);

  const startTour = useCallback(
    (flowId) => {
      const resolvedId = flowId || flowForPath(location.pathname)?.id || "home";
      setActiveFlowId(resolvedId);
      setStepIndex(0);
    },
    [flowForPath, location.pathname]
  );

  const nextStep = useCallback(() => {
    if (!activeFlow) return;
    if (stepIndex + 1 >= activeFlow.steps.length) {
      finishTour();
    } else {
      setStepIndex((i) => i + 1);
    }
  }, [activeFlow, stepIndex, finishTour]);

  const prevStep = useCallback(() => setStepIndex((i) => Math.max(0, i - 1)), []);

  const value = {
    isActive,
    stepIndex,
    step: isActive ? activeFlow.steps[stepIndex] : null,
    totalSteps: activeFlow ? activeFlow.steps.length : 0,
    startTour,
    nextStep,
    prevStep,
    skipTour: finishTour,
  };

  return <TourContext.Provider value={value}>{children}</TourContext.Provider>;
}

export function useTour() {
  const ctx = useContext(TourContext);
  if (!ctx) {
    throw new Error("useTour precisa ser usado dentro de um TourProvider");
  }
  return ctx;
}
