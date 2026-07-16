@extends('layouts.app')

@section('content')
<div class="reportes-container">
    <!-- Elementos decorativos de café - TAZAS BLANCAS (igual que en inventario y ventas) -->
    <div class="coffee-elements">
        <div class="coffee-cup cup-1">
            <div class="cup-top white-cup"></div>
            <div class="cup-body white-cup"></div>
            <div class="cup-handle white-handle"></div>
            <div class="steam s1"></div>
            <div class="steam s2"></div>
            <div class="steam s3"></div>
        </div>
        <div class="coffee-cup cup-2">
            <div class="cup-top white-cup"></div>
 <div class="cup-body white-cup"></div>
            <div class="cup-handle white-handle"></div>
            <div class="steam s1"></div>
            <div class="steam s2"></div>
            <div class="steam s3"></div>
        </div>
        <div class="coffee-cup cup-3">
            <div class="cup-top white-cup"></div>
            <div class="cup-body white-cup"></div>
            <div class="cup-handle white-handle"></div>
            <div class="steam s1"></div>
            <div class="steam s2"></div>
            <div class="steam s3"></div>
        </div>
        <div class="coffee-bean bean-1"></div>
        <div class="coffee-bean bean-2"></div>
        <div class="coffee-bean bean-3"></div>
        <div class="coffee-bean bean-4"></div>
        <div class="coffee-bean bean-5"></div>
        <div class="particle particle-1"></div>
        <div class="particle particle-2"></div>
        <div class="particle particle-3"></div>
    </div>

    <div class="container py-4">
        <!-- Header con estilo igual al de inventario y ventas -->
        <div class="reportes-header">
            <div class="header-icon">
                <i class="fas fa-chart-line"></i>
            </div>
            <div class="header-title">
                <h4><i class="fas fa-coffee"></i> Reportes de Hoy</h4>
                <p>Resumen de ventas y productos estrella del día</p>
            </div>
            <div class="coffee-decoration-header">
                <span>📈</span>
                <span>☕</span>
                <span>📊</span>
            </div>
            <a href="{{ route('ventas.index') }}" class="btn-ver-historial">
                <i class="fas fa-history me-1"></i> Ver Historial
            </a>
        </div>

        <!-- Tarjeta principal -->
        <div class="reportes-card">
            <!-- Resumen de ventas - Tarjetas superiores con estilo mejorado -->
            <div class="resumen-ventas">
                <div class="resumen-card total">
                    <div class="card-icono">
                        <i class="fas fa-money-bill-wave"></i>
                    </div>
                    <div class="card-contenido">
                        <span class="card-label">Total Vendido Hoy</span>
                        <span class="card-valor">${{ number_format($totalHoy, 2) }}</span>
                    </div>
                </div>
                <div class="resumen-card tickets">
                    <div class="card-icono">
                        <i class="fas fa-receipt"></i>
                    </div>
                    <div class="card-contenido">
                        <span class="card-label">Tickets Generados</span>
                        <span class="card-valor">{{ $ventasHoy->count() }}</span>
                    </div>
                </div>
            </div>

            <!-- Sección de gráfico y detalle -->
            <div class="row g-4">
                <!-- Gráfico de productos más vendidos -->
                <div class="col-lg-5">
                    <div class="grafico-card">
                        <h5 class="grafico-titulo">
                            <i class="fas fa-crown me-2" style="color: #D4AF37;"></i>
                            Top 5 Productos de Hoy
                        </h5>
                        <div class="grafico-contenedor">
                            <canvas id="graficaProductos"></canvas>
                        </div>
                        @if(count($masVendidos) == 0)
                            <p class="text-center text-muted mt-4">No hay ventas registradas hoy.</p>
                        @endif
                    </div>
                </div>

                <!-- Detalle de ventas del día -->
                <div class="col-lg-7">
                    <div class="detalle-card">
                        <h5 class="detalle-titulo">
                            <i class="fas fa-clock me-2" style="color: #8B4513;"></i>
                            Detalle de Ventas - {{ date('d/m/Y') }}
                        </h5>
                        <div class="table-responsive">
                            <table class="table detalle-table">
                                <thead>
                                    <tr>
                                        <th>Hora</th>
                                        <th>Mesa</th>
                                        <th class="text-end">Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    @forelse($ventasHoy as $venta)
                                    <tr>
                                        <td data-label="Hora">
                                            <span class="hora-badge">{{ $venta->created_at->format('h:i A') }}</span>
                                        </td>
                                        <td data-label="Mesa">
                                            <span class="mesa-badge">Mesa {{ $venta->mesa }}</span>
                                        </td>
                                        <td data-label="Total" class="text-end">
                                            <span class="total-badge">${{ number_format($venta->total, 2) }}</span>
                                        </td>
                                    </tr>
                                    @empty
                                    <tr>
                                        <td colspan="3" class="text-center py-4">
                                            <div class="empty-state-small">
                                                <i class="fas fa-receipt fa-2x mb-2" style="color: #d9b382;"></i>
                                                <p class="text-muted">Sin ventas aún</p>
                                            </div>
                                        </td>
                                    </tr>
                                    @endforelse
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ===== TOP 5 PRODUCTOS DEL MES (Spark ML) ===== -->
@if(count($productosMes) > 0)
<div class="ml-section mt-4">
    <h5 class="detalle-titulo">
        <i class="fas fa-chart-bar me-2" style="color:#8B4513;"></i>
        Top 5 Productos del Mes
        <small class="ms-2" style="font-size:0.75rem;color:#a0856b;font-weight:400;">Análisis Spark ML · Top 10</small>
    </h5>
    <div class="grafico-card">
        <div class="grafico-contenedor" style="height:280px;">
            <canvas id="graficaProductosMes"></canvas>
        </div>
    </div>
</div>
@endif



{{-- ===== TABLA CLIENTES FRECUENTES DEL MES ===== --}}
@if(count($clientesFrecuentes) > 0)
<div class="ml-section mt-4">
    <h5 class="detalle-titulo">
        <i class="fas fa-users me-2" style="color:#8B4513;"></i>
        Clientes Frecuentes del Mes
    </h5>
    <div class="grafico-card">
        <div class="table-responsive">
            <table class="table detalle-table">
                <thead>
                    <tr>
                        <th style="width:60px;">Pos.</th>
                        <th>Cliente</th>
                        <th class="text-center">Compras</th>
                        <th class="text-end">Total gastado</th>
                    </tr>
                </thead>
                <tbody>
                    @foreach($clientesFrecuentes as $cliente)
                    <tr>
                        <td data-label="Pos.">
                            @if($loop->iteration == 1)
                                <span style="font-size:1.3rem;">🥇</span>
                            @elseif($loop->iteration == 2)
                                <span style="font-size:1.3rem;">🥈</span>
                            @elseif($loop->iteration == 3)
                                <span style="font-size:1.3rem;">🥉</span>
                            @else
                                <span class="hora-badge">{{ $loop->iteration }}</span>
                            @endif
                        </td>
                        <td data-label="Cliente">
                            <span style="font-weight:600;color:#3E2723;">{{ $cliente['nombre'] }}</span>
                        </td>
                        <td data-label="Compras" class="text-center">
                            <span class="mesa-badge">{{ $cliente['num_compras'] }} {{ $cliente['num_compras'] == 1 ? 'vez' : 'veces' }}</span>
                        </td>
                        <td data-label="Total" class="text-end">
                            <span class="total-badge">${{ number_format($cliente['total_gastado'], 2) }}</span>
                        </td>
                    </tr>
                    @endforeach
                </tbody>
            </table>
        </div>
        <p class="text-muted mt-2" style="font-size:0.8rem;text-align:right;">
            <i class="fas fa-info-circle me-1"></i>
            Datos del mes actual · Generados por el modelo ML
        </p>
    </div>
</div>
@endif

{{-- ===== PREDICCIÓN PRÓXIMA SEMANA ===== --}}
@if($prediccionSemana && (count($prediccionSemana['mas_vendidos'] ?? []) > 0 || count($prediccionSemana['menos_vendidos'] ?? []) > 0))
<div class="ml-section mt-4">
    <h5 class="detalle-titulo">
        <i class="fas fa-chart-line me-2" style="color:#8B4513;"></i>
        Predicción de Ventas — Próxima Semana
        <small class="ms-2" style="font-size:0.75rem;color:#a0856b;font-weight:400;">Basado en promedio del último mes · Spark ML</small>
    </h5>
    <div class="row g-4">

        {{-- Más vendidos --}}
        <div class="col-lg-6">
            <div class="grafico-card h-100">
                <h6 class="grafico-titulo mb-3">
                    <span style="font-size:1.1rem;">🚀</span>
                    <span class="ms-2" style="color:#155724;">Top 5 — Se venderán más</span>
                </h6>
                <div class="table-responsive">
                    <table class="table detalle-table mb-0">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Producto</th>
                                <th class="text-center">Prom. semanal</th>
                                <th class="text-end">Predicción</th>
                            </tr>
                        </thead>
                        <tbody>
                            @foreach($prediccionSemana['mas_vendidos'] as $i => $p)
                            <tr>
                                <td><span class="hora-badge">{{ $i + 1 }}</span></td>
                                <td><span style="font-weight:600;color:#3E2723;">{{ $p['nombre'] }}</span></td>
                                <td class="text-center">
                                    <span class="mesa-badge">{{ $p['promedio_semanal'] ?? '—' }} u/sem</span>
                                </td>
                                <td class="text-end">
                                    <span style="font-weight:700;color:#155724;">≈ {{ $p['prediccion'] }} u</span>
                                </td>
                            </tr>
                            @endforeach
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        {{-- Menos vendidos --}}
        <div class="col-lg-6">
            <div class="grafico-card h-100">
                <h6 class="grafico-titulo mb-3">
                    <span style="font-size:1.1rem;">📉</span>
                    <span class="ms-2" style="color:#856404;">Bottom 5 — Se venderán menos</span>
                </h6>
                <div class="table-responsive">
                    <table class="table detalle-table mb-0">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Producto</th>
                                <th class="text-center">Prom. semanal</th>
                                <th class="text-end">Predicción</th>
                            </tr>
                        </thead>
                        <tbody>
                            @foreach($prediccionSemana['menos_vendidos'] as $i => $p)
                            <tr>
                                <td><span class="hora-badge">{{ $i + 1 }}</span></td>
                                <td><span style="font-weight:600;color:#3E2723;">{{ $p['nombre'] }}</span></td>
                                <td class="text-center">
                                    <span class="mesa-badge">{{ $p['promedio_semanal'] ?? '—' }} u/sem</span>
                                </td>
                                <td class="text-end">
                                    <span style="font-weight:700;color:#856404;">≈ {{ $p['prediccion'] }} u</span>
                                </td>
                            </tr>
                            @endforeach
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

    </div>
    <p class="text-muted mt-2" style="font-size:0.8rem;text-align:right;">
        <i class="fas fa-info-circle me-1"></i>
        Predicción basada en el promedio de ventas semanales del último mes + tendencia del 5%
    </p>
</div>
@endif

{{-- ===== COMBOS RECOMENDADOS (K-Means) ===== --}}
@if(count($combos) > 0)
<div class="ml-section mt-4">
    <h5 class="detalle-titulo">
        <i class="fas fa-layer-group me-2" style="color:#8B4513;"></i>
        Combos Recomendados
        <small class="ms-2" style="font-size:0.75rem;color:#a0856b;font-weight:400;">
            Análisis de historial de ventas · Top {{ count($combos) }}
        </small>
    </h5>
    <div class="grafico-card">
        <div class="table-responsive">
            <table class="table detalle-table">
                <thead>
                    <tr>
                        <th style="width:60px;">Pos.</th>
                        <th>Combo</th>
                        <th class="text-center">Frecuencia</th>
                        <th class="text-center">% Apariciones</th>
                        <th class="text-end">Precio normal</th>
                        <th class="text-center">Descuento</th>
                        <th class="text-end">Precio sugerido</th>
                        <th class="text-end">Ahorro</th>
                        <th>Recomendación</th>
                    </tr>
                </thead>
                <tbody>
                    @foreach($combos as $item)
                    <tr>
                        <td data-label="Pos.">
                            @if($item['posicion'] == 1)
                                <span style="font-size:1.3rem;">🥇</span>
                            @elseif($item['posicion'] == 2)
                                <span style="font-size:1.3rem;">🥈</span>
                            @elseif($item['posicion'] == 3)
                                <span style="font-size:1.3rem;">🥉</span>
                            @else
                                <span class="hora-badge">{{ $item['posicion'] }}</span>
                            @endif
                        </td>
                        <td data-label="Combo">
                            <span style="font-weight:600;color:#3E2723;">{{ $item['combo'] }}</span>
                        </td>
                        <td data-label="Frecuencia" class="text-center">
                            <span class="mesa-badge">{{ $item['frecuencia'] }}</span>
                        </td>
                        <td data-label="% Apariciones" class="text-center">
                            {{ $item['porcentaje_aparicion'] }}%
                        </td>
                        <td data-label="Precio normal" class="text-end">
                            ${{ number_format($item['precio_normal'], 2) }}
                        </td>
                        <td data-label="Descuento" class="text-center">
                            <span class="mesa-badge">{{ $item['descuento_sugerido'] }}%</span>
                        </td>
                        <td data-label="Precio sugerido" class="text-end">
                            <span class="total-badge">${{ number_format($item['precio_combo_sugerido'], 2) }}</span>
                        </td>
                        <td data-label="Ahorro" class="text-end" style="color:#28a745;font-weight:700;">
                            ${{ number_format($item['ahorro_cliente'], 2) }}
                        </td>
                        <td data-label="Recomendación">
                            <span style="font-size:0.85rem;">{{ $item['recomendacion'] }}</span>
                            <br>
                            <small style="color:#a0856b;">{{ $item['recomendacion_tipo'] }}</small>
                        </td>
                    </tr>
                    @endforeach
                </tbody>
            </table>
        </div>
        <p class="text-muted mt-2" style="font-size:0.8rem;text-align:right;">
            <i class="fas fa-info-circle me-1"></i>
            Basado en {{ $combos[0]['ventas_analizadas'] ?? 0 }} ventas analizadas ·
            {{ $combos[0]['ventas_con_dos_o_mas_productos'] ?? 0 }} con 2+ productos
        </p>
    </div>
    {{-- ===== SEGMENTACIÓN DE CLIENTES: PCA ===== --}}
@if(!empty($segmentacionPca) && !empty($segmentacionPca['clientes']))

<div class="ml-section mt-4">

    {{-- Encabezado --}}
    <h5 class="detalle-titulo">
        <i class="fas fa-brain me-2" style="color:#8B4513;"></i>
        Segmentación de Clientes — PCA
        <small class="ms-2" style="font-size:0.75rem;color:#a0856b;font-weight:400;">
            Análisis de Componentes Principales · {{ $segmentacionPca['total_clientes'] }} clientes
        </small>
    </h5>

    {{-- Tarjetas de resumen PCA --}}
    <div class="row g-3 mb-4">
        <div class="col-sm-6 col-lg-3">
            <div class="grafico-card text-center py-3">
                <div style="font-size:2rem;color:#8B4513;"><i class="fas fa-users"></i></div>
                <div style="font-size:1.8rem;font-weight:700;color:#3E2723;">
                    {{ $segmentacionPca['total_clientes'] }}
                </div>
                <div style="color:#8B6B4F;font-size:.85rem;text-transform:uppercase;letter-spacing:.5px;">
                    Clientes analizados
                </div>
            </div>
        </div>
        <div class="col-sm-6 col-lg-3">
            <div class="grafico-card text-center py-3">
                <div style="font-size:2rem;color:#8B4513;"><i class="fas fa-compress-arrows-alt"></i></div>
                <div style="font-size:1.8rem;font-weight:700;color:#3E2723;">
                    {{ $segmentacionPca['n_componentes_pca'] }}
                </div>
                <div style="color:#8B6B4F;font-size:.85rem;text-transform:uppercase;letter-spacing:.5px;">
                    Componentes PCA
                </div>
            </div>
        </div>
        <div class="col-sm-6 col-lg-3">
            <div class="grafico-card text-center py-3">
                <div style="font-size:2rem;color:#8B4513;"><i class="fas fa-percentage"></i></div>
                <div style="font-size:1.8rem;font-weight:700;color:#3E2723;">
                    {{ round($segmentacionPca['varianza_acumulada_pca'] * 100, 1) }}%
                </div>
                <div style="color:#8B6B4F;font-size:.85rem;text-transform:uppercase;letter-spacing:.5px;">
                    Varianza explicada
                </div>
            </div>
        </div>
        <div class="col-sm-6 col-lg-3">
            <div class="grafico-card text-center py-3">
                <div style="font-size:2rem;color:#8B4513;"><i class="fas fa-layer-group"></i></div>
                <div style="font-size:1.8rem;font-weight:700;color:#3E2723;">
                    {{ count($segmentacionPca['features_usadas']) }}
                </div>
                <div style="color:#8B6B4F;font-size:.85rem;text-transform:uppercase;letter-spacing:.5px;">
                    Features usadas
                </div>
            </div>
        </div>
    </div>

    <div class="row g-4">

        {{-- Gráfica de dispersión PCA --}}
        <div class="col-lg-7">
            <div class="grafico-card">
                <h6 class="grafico-titulo mb-3">
                    <i class="fas fa-project-diagram me-2" style="color:#8B4513;"></i>
                    Mapa de clientes en espacio PCA
                    <small style="font-weight:400;color:#a0856b;">
                        · PC1 {{ round($segmentacionPca['varianza_por_componente'][0] * 100, 1) }}%
                        · PC2 {{ round($segmentacionPca['varianza_por_componente'][1] * 100, 1) }}%
                    </small>
                </h6>
                {{-- Etiquetas de ejes --}}
                <div style="text-align:center;margin-bottom:4px;">
                    <small style="color:#8B6B4F;">
                        <strong>PC1</strong> =
                        {{ $segmentacionPca['interpretacion_componentes'][0]['interpretacion'] ?? '—' }}
                        &nbsp;|&nbsp;
                        <strong>PC2</strong> =
                        {{ $segmentacionPca['interpretacion_componentes'][1]['interpretacion'] ?? '—' }}
                    </small>
                </div>
                <div style="position:relative;height:320px;">
                    <canvas id="graficaPCA"></canvas>
                </div>
            </div>
        </div>

        {{-- Tabla de clientes con coordenadas --}}
        <div class="col-lg-5">
            <div class="grafico-card h-100">
                <h6 class="grafico-titulo mb-3">
                    <i class="fas fa-list-ol me-2" style="color:#8B4513;"></i>
                    Perfil de clientes
                </h6>
                <div class="table-responsive">
                    <table class="table detalle-table" style="font-size:.85rem;">
                        <thead>
                            <tr>
                                <th>Cliente</th>
                                <th class="text-center">Visitas</th>
                                <th class="text-end">Gasto total</th>
                                <th class="text-center">PC1</th>
                                <th class="text-center">PC2</th>
                            </tr>
                        </thead>
                        <tbody>
                            @foreach($segmentacionPca['clientes'] as $cliente)
                            <tr>
                                <td>
                                    <span style="font-weight:600;color:#3E2723;">
                                        {{ $cliente['nombre'] }}
                                    </span>
                                </td>
                                <td class="text-center">
                                    <span class="mesa-badge">{{ $cliente['frecuencia'] }}</span>
                                </td>
                                <td class="text-end">
                                    <span class="total-badge">
                                        ${{ number_format($cliente['gasto_total'], 0) }}
                                    </span>
                                </td>
                                <td class="text-center">
                                    @php $pc1 = $cliente['pc1']; @endphp
                                    <span style="color:{{ $pc1 > 0 ? '#155724' : '#721c24' }};font-weight:600;">
                                        {{ number_format($pc1, 2) }}
                                    </span>
                                </td>
                                <td class="text-center">
                                    @php $pc2 = $cliente['pc2']; @endphp
                                    <span style="color:{{ $pc2 > 0 ? '#155724' : '#721c24' }};font-weight:600;">
                                        {{ number_format($pc2, 2) }}
                                    </span>
                                </td>
                            </tr>
                            @endforeach
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

    </div>

    {{-- Varianza por componente — barras --}}
    <div class="grafico-card mt-4">
        <h6 class="grafico-titulo mb-3">
            <i class="fas fa-chart-bar me-2" style="color:#8B4513;"></i>
            Varianza explicada por componente
        </h6>
        <div style="height:140px;">
            <canvas id="graficaVarianza"></canvas>
        </div>
    </div>

    {{-- Interpretación de componentes --}}
    <div class="row g-3 mt-1">
        @foreach($segmentacionPca['interpretacion_componentes'] as $comp)
        <div class="col-md-6">
            <div class="grafico-card">
                <h6 style="color:#5D4037;font-weight:700;margin-bottom:12px;">
                    <span style="background:#8B4513;color:white;padding:2px 10px;border-radius:20px;font-size:.8rem;margin-right:8px;">
                        {{ $comp['componente'] }}
                    </span>
                    {{ $comp['interpretacion'] }}
                </h6>
                <div style="display:flex;flex-direction:column;gap:8px;">
                    @foreach($comp['features_top'] as $feat)
                    @php
                        $peso    = $feat['peso'];
                        $pctBar  = min(abs($peso) * 100, 100);
                        $color   = $peso >= 0 ? '#8B4513' : '#dc3545';
                        $bgBar   = $peso >= 0 ? 'rgba(139,69,19,.15)' : 'rgba(220,53,69,.1)';
                    @endphp
                    <div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                            <small style="color:#5D4037;font-weight:600;">{{ $feat['feature'] }}</small>
                            <small style="color:{{ $color }};font-weight:700;">
                                {{ $peso >= 0 ? '+' : '' }}{{ number_format($peso, 3) }}
                            </small>
                        </div>
                        <div style="background:#f0e8dc;border-radius:20px;height:8px;overflow:hidden;">
                            <div style="width:{{ $pctBar }}%;height:100%;background:{{ $color }};border-radius:20px;transition:width .6s ease;"></div>
                        </div>
                    </div>
                    @endforeach
                </div>
                <p class="text-muted mt-2 mb-0" style="font-size:.78rem;">
                    <i class="fas fa-info-circle me-1"></i>
                    Peso positivo: la feature empuja al cliente hacia valores altos en este componente.
                    Peso negativo: la feature lo aleja.
                </p>
            </div>
        </div>
        @endforeach
    </div>

    <p class="text-muted mt-3" style="font-size:0.8rem;text-align:right;">
        <i class="fas fa-info-circle me-1"></i>
        Generado por PCA con sklearn · Features normalizadas con Z-score ·
        Varianza acumulada: {{ round($segmentacionPca['varianza_acumulada_pca'] * 100, 1) }}%
    </p>

    {{-- ===== SEGMENTOS DE CLIENTES ===== --}}
    @if(!empty($segmentosEtiquetados))
    <hr style="border-color:#e8d5c0;margin:30px 0;">
    <h6 class="grafico-titulo mb-4">
        <i class="fas fa-users-cog me-2" style="color:#8B4513;"></i>
        Segmentos Detectados
        <small class="ms-2" style="font-size:.75rem;color:#a0856b;font-weight:400;">
            Basado en K-Means · {{ array_sum(array_map(fn($s) => count($s['clientes']), $segmentosEtiquetados)) }} clientes clasificados
        </small>
    </h6>

    <div class="row g-3">
        {{-- Columna izquierda: tarjetas de segmentos --}}
        <div class="col-lg-6">
            <div style="display:flex;flex-direction:column;gap:12px;">
                @foreach($segmentosEtiquetados as $tipo => $seg)
                <div class="seg-card" style="border-color:{{ $seg['border'] }};background:{{ $seg['bg'] }};">
                    <div class="seg-card-header">
                        <span class="seg-card-icono">{{ $seg['icono'] }}</span>
                        <div>
                            <span class="seg-card-titulo" style="color:{{ $seg['color'] }};">
                                {{ $seg['etiqueta'] }}
                            </span>
                            <span class="seg-card-count">
                                {{ count($seg['clientes']) }} {{ count($seg['clientes']) === 1 ? 'cliente' : 'clientes' }}
                            </span>
                        </div>
                    </div>
                    {{-- Chips de clientes --}}
                    <div class="seg-chips">
                        @foreach($seg['clientes'] as $cli)
                        <span class="seg-chip" style="border-color:{{ $seg['border'] }};color:{{ $seg['color'] }};">
                            {{ $cli['nombre'] }}
                            <small style="opacity:.7;margin-left:4px;">
                                {{ $cli['frecuencia'] }}x · ${{ number_format($cli['gasto_total'], 0) }}
                            </small>
                        </span>
                        @endforeach
                    </div>
                </div>
                @endforeach
            </div>
        </div>

        {{-- Columna derecha: campañas de marketing --}}
        <div class="col-lg-6">
            <div class="grafico-card h-100">
                <h6 class="grafico-titulo mb-3">
                    <i class="fas fa-bullhorn me-2" style="color:#8B4513;"></i>
                    Campañas de Marketing Sugeridas
                </h6>
                <div style="display:flex;flex-direction:column;gap:10px;">
                    @foreach($segmentosEtiquetados as $tipo => $seg)
                    <div class="seg-campaign" style="border-left-color:{{ $seg['border'] }};">
                        <span style="font-size:1.1rem;">{{ $seg['icono'] }}</span>
                        <div>
                            <span style="font-weight:700;color:#3E2723;">{{ $seg['etiqueta'] }}</span>
                            <span style="color:#5D4037;font-size:.88rem;display:block;">
                                {{ $seg['accion'] }}
                            </span>
                        </div>
                    </div>
                    @endforeach
                </div>
            </div>
        </div>
    </div>
    @endif

</div>

@else
<div class="mt-4 p-4 rounded-4 text-center" style="background:#fff8f0;border:1px dashed #d9b382;">
    <i class="fas fa-brain fa-2x mb-2" style="color:#d9b382;"></i>
    <p style="color:#8B6B4F;margin:0;">
        No hay datos de segmentación PCA. Ejecuta
        <code>python segmentacion_clientes.py</code> desde la carpeta <code>api/</code>.
    </p>
</div>
@endif

</div>
@else
<div class="mt-4 p-4 rounded-4 text-center" style="background:#fff8f0;border:1px dashed #d9b382;">
    <i class="fas fa-layer-group fa-2x mb-2" style="color:#d9b382;"></i>
    <p style="color:#8B6B4F;margin:0;">
        Aún no hay combos detectados. Ejecuta el análisis de combos para generar recomendaciones.
    </p>
</div>
@endif

</div>

<!-- Scripts para Chart.js (igual que antes) -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        @if(count($masVendidos) > 0)
        const ctx = document.getElementById('graficaProductos').getContext('2d');
        const nombres = {!! json_encode(array_keys($masVendidos)) !!};
        const cantidades = {!! json_encode(array_values($masVendidos)) !!};

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: nombres,
                datasets: [{
                    data: cantidades,
                    backgroundColor: [
                        '#8B4513', // Café Oscuro
                        '#D2691E', // Chocolate
                        '#D4AF37', // Dorado
                        '#A0522D', // Sienna
                        '#5D4037'  // Marrón
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: { size: 12 }
                        }
                    }
                },
                cutout: '65%'
            }
        });
        @endif

        @if(count($productosMes) > 0)
        const ctxMes = document.getElementById('graficaProductosMes').getContext('2d');
        const nombresMes   = {!! json_encode(array_column($productosMes, 'nombre')) !!};
        const cantidadesMes = {!! json_encode(array_column($productosMes, 'cantidad')) !!};

        new Chart(ctxMes, {
            type: 'doughnut',
            data: {
                labels: nombresMes,
                datasets: [{
                    data: cantidadesMes,
                    backgroundColor: [
                        '#8B4513',
                        '#D2691E',
                        '#D4AF37',
                        '#A0522D',
                        '#5D4037',
                        '#C0874F',
                        '#E8A87C',
                        '#6D3B1F',
                        '#B8860B',
                        '#8B6914'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: { size: 12 }
                        }
                    }
                },
                cutout: '65%'
            }
        });
        @endif
        // ── Gráfica PCA: dispersión PC1 vs PC2 ──────────────────────────────
@if(!empty($segmentacionPca['clientes']))
const pcaClientes = @json($segmentacionPca['clientes']);
const coloresPca  = [
    '#8B4513','#D2691E','#D4AF37','#A0522D','#5D4037',
    '#C0874F','#E8A87C','#6D3B1F','#B8860B','#8B6914'
];
new Chart(document.getElementById('graficaPCA'), {
    type: 'scatter',
    data: {
        datasets: [{
            label: 'Clientes',
            data: pcaClientes.map(c => ({ x: c.pc1, y: c.pc2, nombre: c.nombre, frecuencia: c.frecuencia, gasto: c.gasto_total })),
            backgroundColor: pcaClientes.map((_, i) => coloresPca[i % coloresPca.length]),
            pointRadius: 10,
            pointHoverRadius: 14,
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: ctx => [
                        `${ctx.raw.nombre}`,
                        `PC1: ${ctx.raw.x.toFixed(3)}  PC2: ${ctx.raw.y.toFixed(3)}`,
                        `Frecuencia: ${ctx.raw.frecuencia}  Gasto: $${ctx.raw.gasto.toLocaleString()}`
                    ]
                }
            }
        },
        scales: {
            x: { title: { display: true, text: 'PC1 — {{ $segmentacionPca["interpretacion_componentes"][0]["interpretacion"] ?? "Componente 1" }}' } },
            y: { title: { display: true, text: 'PC2 — {{ $segmentacionPca["interpretacion_componentes"][1]["interpretacion"] ?? "Componente 2" }}' } }
        }
    }
});
@endif

// ── Gráfica WCSS: método del codo ───────────────────────────────────
@if(!empty($segmentacionWcss['wcss_por_k']))
const wcssData   = @json($segmentacionWcss['wcss_por_k']);
const kOptimo    = {{ $segmentacionWcss['k_optimo'] ?? 'null' }};
new Chart(document.getElementById('graficaWCSS'), {
    type: 'line',
    data: {
        labels: wcssData.map(d => `K=${d.k}`),
        datasets: [{
            label: 'WCSS',
            data: wcssData.map(d => d.wcss),
            borderColor: '#8B4513',
            backgroundColor: wcssData.map(d => d.k === kOptimo ? 'rgba(139,69,19,0.8)' : 'rgba(139,69,19,0.2)'),
            borderWidth: 2,
            pointRadius: wcssData.map(d => d.k === kOptimo ? 10 : 5),
            pointHoverRadius: 12,
            tension: 0.3,
            fill: false,
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            tooltip: {
                callbacks: {
                    label: ctx => {
                        const label = `WCSS: ${ctx.raw.toFixed(3)}`;
                        return ctx.label === `K=${kOptimo}` ? label + '  ← K óptimo' : label;
                    }
                }
            }
        },
        scales: {
            x: { title: { display: true, text: 'Número de clusters (K)' } },
            y: { title: { display: true, text: 'WCSS (inercia)' } }
        }
    }
});
@endif

// ── Gráfica varianza explicada por componente ────────────────────────
@if(!empty($segmentacionPca['varianza_por_componente']))
new Chart(document.getElementById('graficaVarianza'), {
    type: 'bar',
    data: {
        labels: @json(array_map(fn($i) => 'PC' . ($i + 1), array_keys($segmentacionPca['varianza_por_componente']))),
        datasets: [{
            label: 'Varianza explicada (%)',
            data: @json(array_map(fn($v) => round($v * 100, 1), $segmentacionPca['varianza_por_componente'])),
            backgroundColor: ['rgba(139,69,19,0.8)', 'rgba(210,105,30,0.7)', 'rgba(212,175,55,0.6)',
                              'rgba(160,82,45,0.5)', 'rgba(93,64,55,0.4)'],
            borderRadius: 8,
            borderSkipped: false,
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: ctx => `Varianza: ${ctx.raw}%`
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                ticks: { callback: v => v + '%' },
                title: { display: true, text: 'Varianza (%)' }
            }
        }
    }
});
@endif

    });

    // ML Predicción
document.getElementById('btn-predecir')?.addEventListener('click', function () {
    const cantidad = document.getElementById('ml-cantidad').value;
    const precio   = document.getElementById('ml-precio').value;

    document.getElementById('ml-resultado').style.display = 'none';
    document.getElementById('ml-loading').style.display   = 'block';

    fetch('{{ route("ventas.predecir") }}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': '{{ csrf_token() }}'
        },
        body: JSON.stringify({ cantidad: parseFloat(cantidad), precio: parseFloat(precio) })
    })
    .then(r => r.json())
    .then(res => {
        document.getElementById('ml-loading').style.display = 'none';
        const box = document.getElementById('ml-resultado');
        box.style.display = 'block';

        if (res.success) {
            const alta = res.data.prediccion === 'alta';
            document.getElementById('ml-resultado-inner').style.background = alta ? '#d4edda' : '#fff3cd';
            document.getElementById('ml-icono').innerHTML  = alta ? '🚀' : '📉';
            document.getElementById('ml-texto').innerHTML  = alta ? 'VENTA ALTA' : 'VENTA BAJA';
            document.getElementById('ml-texto').style.color = alta ? '#155724' : '#856404';
            document.getElementById('ml-detalle').innerHTML =
                `Ingreso estimado: <strong>$${res.data.ingreso}</strong> &nbsp;|&nbsp; Confianza: <strong>$${(res.data.confianza * 100).toFixed(1)}%</strong>`;
        } else {
            document.getElementById('ml-resultado-inner').style.background = '#f8d7da';
            document.getElementById('ml-icono').innerHTML = '⚠️';
            document.getElementById('ml-texto').innerHTML = 'Error al predecir';
            document.getElementById('ml-texto').style.color = '#721c24';
            document.getElementById('ml-detalle').innerHTML = res.error ?? 'Error desconocido';
        }
    })
    .catch(err => {
        document.getElementById('ml-loading').style.display = 'none';
        const box = document.getElementById('ml-resultado');
        box.style.display = 'block';
        document.getElementById('ml-resultado-inner').style.background = '#f8d7da';
        document.getElementById('ml-icono').innerHTML = '⚠️';
        document.getElementById('ml-texto').innerHTML = 'Error de conexión';
        document.getElementById('ml-texto').style.color = '#721c24';
        document.getElementById('ml-detalle').innerHTML = 'No se pudo conectar. Verifica que la API Python esté corriendo.';
    });
});


</script>

<style>

    /* ===== SEGMENTACIÓN DE CLIENTES ===== */
.seg-metric-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 20px 10px;
    background: linear-gradient(145deg, #fff, #f5f0eb);
    border-radius: 18px;
    border: 1px solid rgba(139,69,19,.1);
    height: 100%;
    transition: all .3s;
}
.seg-metric-card:hover { transform: translateY(-4px); box-shadow: 0 10px 25px rgba(139,69,19,.12); }
.seg-metric-icon {
    width: 48px; height: 48px; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; margin-bottom: 4px;
}
.seg-metric-val  { font-size: 2rem; font-weight: 700; color: #3E2723; line-height: 1; }
.seg-metric-label { font-size: .8rem; color: #8B6B4F; text-transform: uppercase; letter-spacing: .4px; font-weight: 600; }
.seg-metric-sub  { font-size: .75rem; color: #a0856b; text-align: center; }

.seg-interp-badge {
    background: #faf5f0; border: 1px solid #e8d5c0;
    border-radius: 12px; padding: 8px 14px;
    display: flex; flex-direction: column; gap: 2px;
}
.seg-interp-badge strong { color: #8B4513; font-size: .85rem; }
.seg-interp-badge span   { color: #3E2723; font-size: .9rem; font-weight: 600; }
.seg-interp-badge small  { color: #a0856b; font-size: .75rem; }

.seg-cluster-card {
    background: white; border-radius: 18px; padding: 20px;
    box-shadow: 0 3px 12px rgba(0,0,0,.06);
    border: 1px solid #e8d5c0; height: 100%;
    transition: all .3s;
}
.seg-cluster-card:hover { transform: translateY(-3px); box-shadow: 0 10px 25px rgba(139,69,19,.12); }
.seg-cluster-header {
    display: flex; align-items: center; gap: 14px; margin-bottom: 14px;
}
.seg-cluster-icon  { font-size: 2.2rem; line-height: 1; }
.seg-cluster-title { font-weight: 700; color: #3E2723; font-size: 1.05rem; }
.seg-cluster-count { font-size: .82rem; color: #8B6B4F; }

.seg-perfil-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px;
}
.seg-perfil-item {
    display: flex; align-items: center; gap: 7px;
    background: #faf5f0; border-radius: 10px; padding: 6px 10px;
    font-size: .82rem; color: #5D4037;
}
.seg-perfil-item i { color: #8B4513; width: 14px; text-align: center; }

.seg-accion {
    background: linear-gradient(145deg, #f5ebe0, #ede0d4);
    border-radius: 10px; padding: 9px 14px;
    font-size: .85rem; color: #5D4037; margin-bottom: 12px;
}
.seg-clientes-lista { display: flex; flex-wrap: wrap; gap: 6px; }
.seg-cliente-chip {
    display: inline-flex; align-items: center; gap: 5px;
    background: #f5ebe0; border: 1px solid #e8d5c0;
    border-radius: 20px; padding: 4px 12px;
    font-size: .8rem; color: #3E2723; font-weight: 600;
}
.seg-cliente-chip small { color: #8B6B4F; font-weight: 400; }

/* ── Tarjetas de segmentos ── */
.seg-card {
    border: 1.5px solid #e8d5c0;
    border-radius: 16px;
    padding: 14px 18px;
    transition: transform .2s, box-shadow .2s;
}
.seg-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,.08); }
.seg-card-header {
    display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
}
.seg-card-icono  { font-size: 1.6rem; line-height: 1; }
.seg-card-titulo { font-weight: 700; font-size: 1rem; display: block; }
.seg-card-count  { font-size: .78rem; color: #8B6B4F; display: block; }
.seg-chips       { display: flex; flex-wrap: wrap; gap: 6px; }
.seg-chip {
    display: inline-flex; align-items: center; gap: 4px;
    border: 1px solid #e8d5c0; border-radius: 20px;
    padding: 4px 12px; font-size: .8rem; font-weight: 600;
    background: rgba(255,255,255,.7);
}
.seg-campaign {
    display: flex; align-items: flex-start; gap: 12px;
    background: #faf5f0; border-radius: 12px; padding: 12px 16px;
    border-left: 4px solid #e8d5c0;
}

    /* ===== ESTILOS DECORATIVOS (mismos que en inventario y ventas) ===== */
    .reportes-container {
        position: relative;
        min-height: 100vh;
        background: linear-gradient(145deg, #faf0e6 0%, #f5e6d3 100%);
        font-family: 'Poppins', 'Segoe UI', sans-serif;
        padding: 20px 0;
        overflow-x: hidden;
    }

    /* Elementos decorativos */
    .coffee-elements {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
    }

    .coffee-cup {
        position: absolute;
        opacity: 0.15;
    }

    .cup-1 { top: 30px; left: 30px; transform: scale(0.7); }
    .cup-2 { bottom: 30px; right: 30px; transform: scale(0.7) rotate(-10deg); }
    .cup-3 { top: 50%; right: 40px; transform: scale(0.6) translateY(-50%); }

    .white-cup { background: linear-gradient(145deg, #ffffff, #f8f8f8) !important; }
    .white-handle { border-color: #f0f0f0 !important; border-right: 6px solid #ffffff !important; }

    .cup-top { width: 60px; height: 15px; border-radius: 50%; background: linear-gradient(145deg, #ffffff, #f0f0f0); }
    .cup-body { width: 50px; height: 45px; border-radius: 0 0 25px 25px; background: linear-gradient(145deg, #ffffff, #f5f5f5); top: -7px; position: relative; }
    .cup-handle { width: 18px; height: 30px; border: 5px solid #f0f0f0; border-left: none; border-radius: 0 15px 15px 0; position: absolute; right: -15px; top: 10px; }

    .steam { position: absolute; background: rgba(255,255,255,0.5); border-radius: 50%; animation: steam 3s infinite; }
    .s1 { width: 10px; height: 10px; top: -15px; left: 15px; }
    .s2 { width: 8px; height: 8px; top: -20px; left: 25px; animation-delay: 0.5s; }
    .s3 { width: 6px; height: 6px; top: -18px; left: 35px; animation-delay: 1s; }

    @keyframes steam {
        0%,100% { transform: translateY(0) scale(1); opacity: 0.5; }
        50% { transform: translateY(-10px) scale(1.2); opacity: 0.2; }
    }

    .coffee-bean {
        position: absolute;
        width: 15px;
        height: 7px;
        background: #8B4513;
        border-radius: 50%;
        opacity: 0.1;
        animation: float 20s infinite linear;
        transform: rotate(45deg);
    }

    .bean-1 { top: 15%; left: 5%; animation-delay: 0s; }
    .bean-2 { bottom: 20%; right: 5%; animation-delay: 5s; }
    .bean-3 { top: 40%; left: 8%; animation-delay: 8s; }
    .bean-4 { bottom: 30%; right: 8%; animation-delay: 12s; }
    .bean-5 { top: 70%; left: 3%; animation-delay: 15s; }

    @keyframes float {
        from { transform: translateY(0) rotate(45deg); opacity: 0.1; }
        to { transform: translateY(-100vh) rotate(405deg); opacity: 0; }
    }

    .particle {
        position: absolute;
        width: 3px;
        height: 3px;
        background: rgba(139,69,19,0.2);
        border-radius: 50%;
        animation: particle-float 15s infinite linear;
    }

    .particle-1 { top: 20%; left: 15%; animation-delay: 0s; }
    .particle-2 { top: 60%; right: 10%; animation-delay: 5s; }
    .particle-3 { top: 80%; left: 20%; animation-delay: 10s; }

    @keyframes particle-float {
        from { transform: translateY(0) scale(1); opacity: 0.3; }
        to { transform: translateY(-100vh) scale(0); opacity: 0; }
    }

    /* Header estilo inventario/ventas */
    .reportes-header {
        background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
        color: white;
        padding: 25px 30px;
        display: flex;
        align-items: center;
        gap: 20px;
        position: relative;
        overflow: hidden;
        border-radius: 30px 30px 0 0;
        z-index: 10;
        flex-wrap: wrap;
    }

    .reportes-header::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 200px;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2));
        transform: skewX(-20deg) translateX(100px);
        animation: shine 3s infinite;
    }

    @keyframes shine {
        0% { transform: skewX(-20deg) translateX(100px); }
        20% { transform: skewX(-20deg) translateX(-200px); }
        100% { transform: skewX(-20deg) translateX(-200px); }
    }

    .header-icon {
        width: 60px;
        height: 60px;
        background: rgba(255,255,255,0.2);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
    }

    .header-title h4 {
        margin: 0;
        font-weight: 700;
        font-size: 1.5rem;
    }

    .header-title p {
        margin: 5px 0 0;
        opacity: 0.9;
        font-size: 0.9rem;
    }

    .coffee-decoration-header {
        margin-left: auto;
        font-size: 1.5rem;
    }

    .coffee-decoration-header span {
        margin: 0 5px;
        animation: bounce 2s infinite;
        display: inline-block;
    }

    @keyframes bounce {
        0%,100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }

    .btn-ver-historial {
        background: rgba(255,255,255,0.2);
        backdrop-filter: blur(5px);
        color: white;
        border: 1px solid rgba(255,255,255,0.3);
        padding: 10px 20px;
        border-radius: 50px;
        text-decoration: none;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        transition: all 0.3s ease;
    }

    .btn-ver-historial:hover {
        background: #D4AF37;
        border-color: #D4AF37;
        color: #2c1a0b;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }

    /* Tarjeta principal */
    .reportes-card {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(10px);
        border-radius: 0 0 30px 30px;
        padding: 30px;
        box-shadow: 0 20px 40px rgba(139, 69, 19, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        z-index: 10;
        position: relative;
    }

    /* Resumen de ventas (tarjetas superiores) */
    .resumen-ventas {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }

    .resumen-card {
        display: flex;
        align-items: center;
        gap: 20px;
        background: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        border: 1px solid rgba(139, 69, 19, 0.1);
        transition: all 0.3s ease;
    }

    .resumen-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(139, 69, 19, 0.15);
    }

    .resumen-card.total .card-icono {
        background: linear-gradient(145deg, #28a745, #218838);
    }

    .resumen-card.tickets .card-icono {
        background: linear-gradient(145deg, #17a2b8, #138496);
    }

    .card-icono {
        width: 60px;
        height: 60px;
        border-radius: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        color: white;
    }

    .card-contenido {
        flex: 1;
    }

    .card-label {
        display: block;
        color: #8B6B4F;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }

    .card-valor {
        display: block;
        font-size: 2rem;
        font-weight: 700;
        color: #3E2723;
    }

    /* Tarjeta del gráfico */
    .grafico-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        height: 100%;
        box-shadow: 0 5px 15px rgba(0,0,0,0.03);
        border: 1px solid rgba(139, 69, 19, 0.1);
    }

    .grafico-titulo {
        color: #5D4037;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
    }

    .grafico-contenedor {
        position: relative;
        height: 300px;
        width: 100%;
    }

    /* Tarjeta de detalle de ventas */
    .detalle-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        height: 100%;
        box-shadow: 0 5px 15px rgba(0,0,0,0.03);
        border: 1px solid rgba(139, 69, 19, 0.1);
    }

    .detalle-titulo {
        color: #5D4037;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
    }

    /* Tabla de detalle */
    .detalle-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 8px;
    }

    .detalle-table thead th {
        background: #f8f4f0;
        color: #5D4037;
        padding: 12px;
        font-weight: 600;
        border-radius: 10px;
    }

    .detalle-table tbody tr {
        background: #faf7f2;
        border-radius: 10px;
        transition: all 0.3s ease;
    }

    .detalle-table tbody tr:hover {
        background: #f0e4d5;
        transform: translateY(-2px);
    }

    .detalle-table tbody td {
        padding: 12px;
        vertical-align: middle;
        border: none;
    }

    .hora-badge {
        background: #8B4513;
        color: white;
        padding: 5px 12px;
        border-radius: 30px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
    }

    .mesa-badge {
        background: #f0e4d5;
        color: #8B4513;
        padding: 5px 12px;
        border-radius: 30px;
        font-size: 0.9rem;
        font-weight: 600;
    }

    .total-badge {
        font-weight: 700;
        color: #28a745;
        font-size: 1.1rem;
    }

    .empty-state-small {
        text-align: center;
        padding: 20px;
    }

    /* Responsividad */
    @media (max-width: 768px) {
        .coffee-cup {
            display: none;
        }

        .reportes-header {
            flex-direction: column;
            text-align: center;
            padding: 20px;
        }

        .coffee-decoration-header {
            margin: 0 auto;
        }

        .btn-ver-historial {
            width: 100%;
            justify-content: center;
        }

        .reportes-card {
            padding: 20px;
        }

        .resumen-ventas {
            grid-template-columns: 1fr;
        }

        .detalle-table thead {
            display: none;
        }

        .detalle-table tbody tr {
            display: block;
            margin-bottom: 15px;
        }

        .detalle-table tbody td {
            display: block;
            text-align: right;
            padding: 10px 15px;
            position: relative;
            border-bottom: 1px solid #eee;
        }

        .detalle-table tbody td:before {
            content: attr(data-label);
            position: absolute;
            left: 15px;
            font-weight: 600;
            color: #8B4513;
        }

        .hora-badge, .mesa-badge, .total-badge {
            display: inline-block;
        }
    }
</style>

<!-- Fonts & Icons -->
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
@endsection
