import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Target, TrendingUp } from 'lucide-react';

import { Card, CardHeader, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/forms/Select';
import { Layout } from '../../components/layout/Layout';
import { api } from '../../services/api';
import { QuestionnaireAnswers, RISK_BUCKETS } from '../../types';

// Validation schema
const riskAssessmentSchema = z.object({
  age: z.number().min(18, 'Debe ser mayor de 18 años').max(100, 'Edad máxima 100 años'),
  horizon: z.string().min(1, 'Seleccione un horizonte de inversión'),
  income: z.string().min(1, 'Seleccione porcentaje de ingresos'),
  knowledge: z.string().min(1, 'Seleccione nivel de conocimiento'),
  max_drop: z.string().min(1, 'Seleccione caída máxima tolerable'),
  reaction: z.string().min(1, 'Seleccione su reacción'),
  liquidity: z.string().min(1, 'Seleccione necesidad de liquidez'),
  goal: z.string().min(1, 'Seleccione objetivo principal'),
  inflation: z.string().min(1, 'Seleccione preocupación por inflación'),
  digital: z.string().min(1, 'Seleccione confianza en plataformas digitales'),
});

type RiskAssessmentForm = z.infer<typeof riskAssessmentSchema>;

const questions = [
  {
    key: 'age' as keyof RiskAssessmentForm,
    title: '¿Cuál es tu edad?',
    type: 'slider',
    min: 18,
    max: 75,
    default: 30,
  },
  {
    key: 'horizon' as keyof RiskAssessmentForm,
    title: '¿Cuál es tu horizonte de inversión?',
    type: 'select',
    options: [
      { value: '< 3 años', label: 'Menos de 3 años' },
      { value: '3-5 años', label: '3 a 5 años' },
      { value: '5-10 años', label: '5 a 10 años' },
      { value: '> 10 años', label: 'Más de 10 años' },
    ],
  },
  {
    key: 'income' as keyof RiskAssessmentForm,
    title: '¿Qué porcentaje de tus ingresos destinas a inversiones?',
    type: 'select',
    options: [
      { value: '< 5 %', label: 'Menos del 5%' },
      { value: '5-10 %', label: '5% al 10%' },
      { value: '10-20 %', label: '10% al 20%' },
      { value: '> 20 %', label: 'Más del 20%' },
    ],
  },
  {
    key: 'knowledge' as keyof RiskAssessmentForm,
    title: '¿Cuál es tu nivel de conocimiento financiero?',
    type: 'select',
    options: [
      { value: 'Principiante', label: 'Principiante' },
      { value: 'Intermedio', label: 'Intermedio' },
      { value: 'Avanzado', label: 'Avanzado' },
    ],
  },
  {
    key: 'max_drop' as keyof RiskAssessmentForm,
    title: '¿Cuál es la máxima caída que tolerarías en tu portafolio?',
    type: 'select',
    options: [
      { value: '5 %', label: '5%' },
      { value: '10 %', label: '10%' },
      { value: '20 %', label: '20%' },
      { value: '30 %', label: '30%' },
      { value: '> 30 %', label: 'Más del 30%' },
    ],
  },
  {
    key: 'reaction' as keyof RiskAssessmentForm,
    title: 'Si tu portafolio cae 15%, ¿qué harías?',
    type: 'select',
    options: [
      { value: 'Vendo todo', label: 'Vendería todo inmediatamente' },
      { value: 'Vendo una parte', label: 'Vendería una parte' },
      { value: 'No hago nada', label: 'No haría nada, esperaría' },
      { value: 'Compro más', label: 'Compraría más aprovechando la baja' },
    ],
  },
  {
    key: 'liquidity' as keyof RiskAssessmentForm,
    title: '¿Cuál es tu necesidad de liquidez?',
    type: 'select',
    options: [
      { value: 'Alta', label: 'Alta - Podría necesitar el dinero pronto' },
      { value: 'Media', label: 'Media - Alguna flexibilidad' },
      { value: 'Baja', label: 'Baja - No necesito el dinero por años' },
    ],
  },
  {
    key: 'goal' as keyof RiskAssessmentForm,
    title: '¿Cuál es tu objetivo principal de inversión?',
    type: 'select',
    options: [
      { value: 'Proteger capital', label: 'Proteger mi capital' },
      { value: 'Ingresos regulares', label: 'Generar ingresos regulares' },
      { value: 'Crecimiento balanceado', label: 'Crecimiento balanceado' },
      { value: 'Máximo crecimiento', label: 'Máximo crecimiento a largo plazo' },
    ],
  },
  {
    key: 'inflation' as keyof RiskAssessmentForm,
    title: '¿Te preocupa la inflación?',
    type: 'select',
    options: [
      { value: 'No me preocupa', label: 'No me preocupa' },
      { value: 'Me preocupa moderadamente', label: 'Me preocupa moderadamente' },
      { value: 'Me preocupa mucho', label: 'Me preocupa mucho' },
    ],
  },
  {
    key: 'digital' as keyof RiskAssessmentForm,
    title: '¿Qué tan cómodo te sientes con plataformas digitales?',
    type: 'select',
    options: [
      { value: 'Baja', label: 'Baja confianza' },
      { value: 'Media', label: 'Confianza media' },
      { value: 'Alta', label: 'Alta confianza' },
    ],
  },
];

export function RiskAssessmentPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [riskResult, setRiskResult] = useState<any>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<RiskAssessmentForm>({
    resolver: zodResolver(riskAssessmentSchema),
    defaultValues: {
      age: 30,
    },
  });

  const watchedValues = watch();
  const currentQuestion = questions[currentStep];
  const isLastStep = currentStep === questions.length - 1;

  const onSubmit = async (data: RiskAssessmentForm) => {
    setIsSubmitting(true);
    try {
      const response = await api.analysis.createRiskProfile(data);
      
      if (response.success && response.data) {
        setRiskResult(response.data);
      } else {
        console.error('Error creating risk profile:', response.error);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const nextStep = () => {
    if (currentStep < questions.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleCreatePortfolio = () => {
    navigate('/portfolio/create');
  };

  // Show results if we have them
  if (riskResult) {
    const riskBucket = RISK_BUCKETS[riskResult.risk_bucket as keyof typeof RISK_BUCKETS];
    
    return (
      <Layout>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card>
            <CardHeader>
              <div className="text-center">
                <Target className="mx-auto h-16 w-16 text-primary-500 mb-4" />
                <h1 className="text-3xl font-bold text-gray-900">
                  Tu Perfil de Riesgo
                </h1>
                <p className="mt-2 text-gray-600">
                  Hemos analizado tus respuestas y determinado tu perfil de inversión
                </p>
              </div>
            </CardHeader>
            
            <CardContent>
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-32 h-32 rounded-full mb-4"
                     style={{ backgroundColor: `${riskBucket.color}20` }}>
                  <TrendingUp className="h-12 w-12" style={{ color: riskBucket.color }} />
                </div>
                
                <h2 className="text-4xl font-bold mb-2" style={{ color: riskBucket.color }}>
                  {riskBucket.label}
                </h2>
                
                <p className="text-lg text-gray-600 mb-4">
                  {riskBucket.description}
                </p>
                
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <div className="flex justify-between items-center text-sm text-gray-600">
                    <span>Puntaje obtenido</span>
                    <span className="font-semibold">
                      {riskResult.total_score}/50
                    </span>
                  </div>
                  <div className="mt-2 bg-gray-200 rounded-full h-3">
                    <div
                      className="h-3 rounded-full transition-all duration-300"
                      style={{
                        width: `${(riskResult.total_score / 50) * 100}%`,
                        backgroundColor: riskBucket.color,
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6 mb-8">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-blue-900 mb-3">
                    Tu Portafolio Recomendado
                  </h3>
                  <div className="space-y-2">
                    {Object.entries(riskResult.model_portfolio || {}).map(([ticker, weight]) => (
                      <div key={ticker} className="flex justify-between">
                        <span className="text-blue-700">{ticker}</span>
                        <span className="font-medium text-blue-900">
                          {((weight as number) * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-green-900 mb-3">
                    Características del Perfil
                  </h3>
                  <ul className="text-green-700 space-y-1">
                    <li>• Nivel de riesgo: {riskResult.risk_label}</li>
                    <li>• Horizonte de inversión optimizado</li>
                    <li>• Diversificación global</li>
                    <li>• Rebalanceo automático sugerido</li>
                  </ul>
                </div>
              </div>

              <div className="text-center">
                <Button
                  onClick={handleCreatePortfolio}
                  size="lg"
                  className="px-8"
                >
                  Crear Mi Portafolio
                </Button>
                
                <p className="mt-4 text-sm text-gray-500">
                  Podrás personalizar las asignaciones más adelante
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardHeader>
            <div className="text-center">
              <h1 className="text-3xl font-bold text-gray-900">
                Análisis de Perfil de Riesgo
              </h1>
              <p className="mt-2 text-gray-600">
                Responde estas preguntas para determinar tu perfil de inversión ideal
              </p>
              
              {/* Progress bar */}
              <div className="mt-6">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Progreso</span>
                  <span>{currentStep + 1} de {questions.length}</span>
                </div>
                <div className="bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${((currentStep + 1) / questions.length) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)}>
              <div className="min-h-[300px] flex flex-col justify-center">
                <div className="text-center mb-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">
                    {currentQuestion.title}
                  </h2>
                  
                  {currentQuestion.type === 'slider' ? (
                    <div className="max-w-md mx-auto">
                      <div className="mb-4">
                        <span className="text-3xl font-bold text-primary-600">
                          {watchedValues.age || currentQuestion.default}
                        </span>
                        <span className="text-gray-500 ml-1">años</span>
                      </div>
                      <input
                        type="range"
                        min={currentQuestion.min}
                        max={currentQuestion.max}
                        value={watchedValues.age || currentQuestion.default}
                        onChange={(e) => setValue('age', parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      />
                      <div className="flex justify-between text-sm text-gray-500 mt-2">
                        <span>{currentQuestion.min}</span>
                        <span>{currentQuestion.max}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="max-w-md mx-auto">
                      <Select
                        options={currentQuestion.options || []}
                        error={errors[currentQuestion.key]?.message}
                        {...register(currentQuestion.key)}
                      />
                    </div>
                  )}
                </div>
              </div>
              
              {/* Navigation buttons */}
              <div className="flex justify-between mt-8">
                <Button
                  type="button"
                  variant="outline"
                  onClick={prevStep}
                  disabled={currentStep === 0}
                >
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Anterior
                </Button>
                
                {isLastStep ? (
                  <Button
                    type="submit"
                    loading={isSubmitting}
                  >
                    Calcular Mi Perfil
                  </Button>
                ) : (
                  <Button
                    type="button"
                    onClick={nextStep}
                  >
                    Siguiente
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}