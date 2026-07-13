@extends('layouts.app')
@section('content')

<div class="inventario-container">
    <div class="coffee-elements">
        <div class="coffee-cup cup-1">
            <div class="cup-top white-cup"></div>
            <div class="cup-body white-cup"></div>
            <div class="cup-handle white-handle"></div>
            <div class="steam s1"></div><div class="steam s2"></div><div class="steam s3"></div>
        </div>
        <div class="coffee-bean bean-1"></div>
        <div class="coffee-bean bean-2"></div>
        <div class="particle particle-1"></div>
    </div>

    <div class="container py-4">

        <!-- Header -->
        <div class="inventario-header">
            <div class="header-icon"><i class="fas fa-chart-line"></i></div>
            <div class="header-title">
                <h4><i class="fas fa-brain"></i> Estadísticas ML — Insumos</h4>
                <p>Regresión lineal: predicción de consumo semanal</p>
            </div>
            <div class="coffee-decoration-header">
                <span>📊</span><span>🤖</span><span>☕</span>
            </div>
            <a href="{{ route('inventario.index') }}" class="btn-nuevo" style="background:rgba(255,255,255,.15);">
                <i class="fas fa-arrow-left me-2"></i> Volver
            </a>
        </div>

        <div class="inventario-card">

            @if(empty($predicciones))
                <div class="empty-state py-5 text-center">
                    <i class="fas fa-robot fa-4x mb-3" style="color:#d9b382;"></i>
                    <h5>No hay predicciones disponibles</h5>
                    <p style="color:#8B6B4F;">Ejecuta <code>python ml_trainer.py</code> desde la carpeta <code>api/</code> para generar los datos.</p>
                </div>
            @else

                <!-- Resumen alertas -->
                @php
                    $alertas = collect($predicciones)->where('alerta', true)->count();
                    $total   = count($predicciones);
                @endphp
                <div class="inventario-resumen mb-4">
                    <div class="resumen-card">
                        <i class="fas fa-flask"></i>
                        <span class="resumen-valor">{{ $total }}</span>
                        <span class="resumen-label">Insumos analizados</span>
                    </div>
                    <div class="resumen-card {{ $alertas > 0 ? 'danger' : '' }}">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span class="resumen-valor">{{ $alertas }}</span>
                        <span class="resumen-label">Stock insuficiente próx. semana</span>
                    </div>
                </div>


                <!-- Gráfica de dispersión: stock actual vs necesidad -->
                <div class="chart-wrapper mb-5">
                    <h5 class="chart-title">
                        <i class="fas fa-circle me-2"></i>
                        Stock actual vs Necesidad semanal (Regresion lineal)
                    </h5>
                    <canvas id="graficaDispersion" height="100"></canvas>
                </div>
                <!-- Tabla detalle desplegable -->
                <div style="border:1px solid #e8d5c0;border-radius:15px;overflow:hidden;margin-bottom:20px;">
                    <table class="table inventario-table" style="margin-bottom:0;">
                        <thead>
                            <tr>
                                <th>Insumo</th>
                                <th>Tipo</th>
                                <th class="text-center">Consumo mes</th>
                                <th class="text-center">Predicción / Error</th>
                                <th class="text-center">Stock actual</th>
                                <th class="text-center">Estado</th>
                            </tr>
                        </thead>

                        <tbody>
                            @foreach($predicciones as $index => $p)
                            <tr class="{{ $index >= 3 ? 'fila-extra' : '' }}" @if($index >= 3) style="display:none;" @endif>
                                <td><strong style="color:#3E2723;">{{ $p['nombre'] }}</strong></td>
                                <td><span class="tipo-badge tipo-{{ $p['tipo'] }}">{{ ucfirst($p['tipo']) }}</span></td>
                                <td class="text-center">{{ number_format($p['consumo_mes'], 3) }}</td>
                                <td class="text-center">
                                    <div class="pred-error-cell">
                                        <div class="pred-real">
                                            <span class="pred-label">Real</span>
                                            <span class="pred-value">{{ number_format($p['necesidad_real'] ?? $p['necesidad_semana'], 3) }}</span>
                                        </div>
                                        <div class="pred-pred">
                                            <span class="pred-label">Pred</span>
                                            <span class="stock-badge {{ $p['alerta'] ? 'bajo' : 'normal' }}">
                                                {{ number_format($p['necesidad_semana'], 3) }}
                                            </span>
                                            @php
                                                $err = $p['error_absoluto'] ?? null;
                                                $errClass = is_null($err) ? 'error-na' : ($err < 0.5 ? 'error-ok' : ($err < 2 ? 'error-warn' : 'error-bad'));
                                                $errLabel = is_null($err) ? 'Sin datos sem.' : 'Δ ' . number_format($err, 3);
                                            @endphp
                                            <span class="error-delta {{ $errClass }}">{{ $errLabel }}</span>

                                        </div>
                                    </div>
                                </td>

                                <td class="text-center">{{ number_format($p['stock_actual'], 3) }}</td>
                                <td class="text-center">
                                    @if($p['alerta'])
                                        <span class="badge-estado agotado">⚠ Stock bajo</span>
                                    @else
                                        <span class="badge-estado normal">✓ Suficiente</span>
                                    @endif
                                </td>
                            </tr>
                            @endforeach
                        </tbody>
                    </table>
                    @if(count($predicciones) > 3)
                    <button class="btn-ver-mas" id="btnVerMas" onclick="toggleDetalle()">
                        <i class="fas fa-chevron-down me-2" id="detalleChevron"></i>
                        Ver todos los insumos ({{ count($predicciones) - 3 }} más)
                    </button>
                    @endif
                </div>



                {{-- ===== ÁRBOL DE DECISIÓN: PROPUESTAS DE VENTA ===== --}}
                @if(!empty($clasificaciones))
                <hr style="border-color:#e8d5c0;margin:40px 0;">

                <h5 class="chart-title mb-1">
                    <i class="fas fa-sitemap me-2"></i> Árbol de Decisión — Propuestas de venta por caducidad
                </h5>
                <p style="color:#8B6B4F;font-size:.9rem;margin-bottom:20px;">
                    Insumos que caducan en los próximos 14 días con propuestas de descuento o paquete para acelerar su rotación.
                </p>

                @php
                    $urgentes = collect($clasificaciones)->where('prediccion', 3)->count();
                    $paquete  = collect($clasificaciones)->where('prediccion', 2)->count();
                    $descInd  = collect($clasificaciones)->where('prediccion', 1)->count();
                @endphp

                <div class="inventario-resumen mb-4">
                    <div class="resumen-card danger">
                        <i class="fas fa-fire"></i>
                        <span class="resumen-valor">{{ $urgentes }}</span>
                        <span class="resumen-label">Liquidar urgente</span>
                    </div>
                    <div class="resumen-card warning">
                        <i class="fas fa-box-open"></i>
                        <span class="resumen-valor">{{ $paquete }}</span>
                        <span class="resumen-label">Descuento por paquete</span>
                    </div>
                    <div class="resumen-card" style="border-color:rgba(23,162,184,.3)">
                        <i class="fas fa-tag" style="color:#17a2b8"></i>
                        <span class="resumen-valor">{{ $descInd }}</span>
                        <span class="resumen-label">Descuento individual</span>
                    </div>
                </div>

                @foreach($clasificaciones as $c)
                <div class="propuesta-card nivel-{{ $c['nivel'] }} mb-3">
                    <div class="propuesta-header">
                        <div class="propuesta-info">
                            <span class="propuesta-nombre">{{ $c['nombre'] }}</span>
                            <span class="propuesta-cad">
                                <i class="fas fa-calendar-times me-1"></i>
                                Caduca: {{ $c['caducidad'] !== 'NA' ? \Carbon\Carbon::parse($c['caducidad'])->format('d/m/Y') : 'N/A' }}
                                @if($c['dias_restantes'] !== null)
                                    <strong>({{ $c['dias_restantes'] }} días)</strong>
                                @endif
                            </span>
                        </div>
                        <div class="propuesta-badge-wrap">
                            @if($c['nivel'] === 'danger')
                                <span class="badge-estado agotado">🔴 {{ $c['clasificacion'] }}</span>
                            @elseif($c['nivel'] === 'warning')
                                <span class="badge-estado bajo">🟡 {{ $c['clasificacion'] }}</span>
                            @elseif($c['nivel'] === 'info')
                                <span class="badge-estado" style="background:#17a2b8;color:white;">🔵 {{ $c['clasificacion'] }}</span>
                            @else
                                <span class="badge-estado normal">🟢 {{ $c['clasificacion'] }}</span>
                            @endif
                            @if($c['descuento_pct'] > 0)
                                <span class="descuento-badge">-{{ $c['descuento_pct'] }}%</span>
                            @endif
                        </div>
                    </div>

                    @if(!empty($c['propuestas']))
                    <div class="propuestas-lista">
                        <small style="color:#8B6B4F;font-weight:600;text-transform:uppercase;letter-spacing:.5px;">
                            <i class="fas fa-lightbulb me-1"></i> Propuestas de venta:
                        </small>
                        <div class="propuestas-grid mt-2">
                            @foreach($c['propuestas'] as $prop)
                            <div class="propuesta-item">
                                <i class="fas fa-store me-1" style="color:#8B4513"></i>
                                <span class="prop-producto">{{ $prop['producto'] }}</span>
                                <span class="prop-texto">{{ $prop['propuesta'] }}</span>
                                <span class="prop-ahorro">Ahorro: ${{ number_format($prop['ahorro'], 2) }}</span>
                            </div>
                            @endforeach
                        </div>
                    </div>
                    @else
                    <div style="padding:10px 0;color:#B2967D;font-size:.9rem;">
                        <i class="fas fa-info-circle me-1"></i> Sin productos asociados a este insumo aún.
                    </div>
                    @endif
                </div>
                @endforeach

                @endif

{{-- ===== MAPREDUCE: CONSUMO POR INSUMO ===== --}}
@if(!empty($mapreduce))
<hr style="border-color:#e8d5c0;margin:40px 0;">

{{-- Encabezado con botón desplegable --}}
<div class="d-flex align-items-center justify-content-between mb-1">
    <h5 class="chart-title mb-0">
        <i class="fas fa-layer-group me-2"></i> MapReduce — Consumo acumulado por insumo
    </h5>
    <button class="btn btn-sm" 
            style="background:#f5ebe0;color:#8B6B4F;border:1px solid #e8d5c0;"
            type="button" 
            data-bs-toggle="collapse" 
            data-bs-target="#mapreduceCollapse" 
            aria-expanded="false">
        <i class="fas fa-chevron-down me-1"></i> Ver tabla
    </button>
</div>
<p style="color:#8B6B4F;font-size:.9rem;margin-bottom:20px;">
    Ranking de productos que más consumen cada insumo, basado en ventas registradas.
</p>

{{-- Resumen (siempre visible) --}}
<div class="inventario-resumen mb-4">
    <div class="resumen-card">
        <i class="fas fa-flask"></i>
        <span class="resumen-valor">{{ count($mapreduce) }}</span>
        <span class="resumen-label">Insumos analizados</span>
    </div>
    <div class="resumen-card">
        <i class="fas fa-chart-line"></i>
        <span class="resumen-valor">{{ collect($mapreduce)->sum('total_consumido') }}</span>
        <span class="resumen-label">Consumo total acumulado</span>
    </div>
</div>

{{-- Tabla colapsable --}}
<div class="collapse" id="mapreduceCollapse">
    <div style="border:1px solid #e8d5c0;border-radius:15px;overflow:hidden;margin-bottom:20px;">
        <table class="table inventario-table" style="margin-bottom:0;">
            <thead>
                <tr>
                    <th>Insumo</th>
                    <th class="text-center">Total consumido</th>
                    <th>Ranking de productos que usan ese insumo</th>
                </tr>
            </thead>
            <tbody>
                @forelse($mapreduce as $item)
                <tr>
                    <td><strong style="color:#3E2723;">
                        <i class="fas fa-leaf me-1" style="color:#8B4513;"></i>
                        {{ $item['insumo'] ?? 'Sin insumo' }}
                    </strong></td>
                    <td class="text-center">
                        <span class="stock-badge normal">
                            <i class="fas fa-chart-simple me-1"></i>{{ $item['total_consumido'] ?? 0 }}
                        </span>
                    </td>
                    <td>
                        @forelse(($item['ranking_productos'] ?? []) as $producto)
                        <div class="mapreduce-ranking-item">
                            <span class="mapreduce-pos">#{{ $producto['posicion'] ?? '-' }}</span>
                            <strong style="color:#3E2723;">{{ $producto['producto'] ?? 'Sin nombre' }}</strong>
                            <span class="mapreduce-detail"><i class="fas fa-box me-1"></i>Vendidos: {{ $producto['cantidad_vendida'] ?? 0 }}</span>
                            <span class="mapreduce-detail"><i class="fas fa-coffee me-1"></i>Consumo est.: {{ $producto['consumo_estimado'] ?? 0 }}</span>
                        </div>
                        @empty
                        <span style="color:#B2967D;font-size:.9rem;">
                            <i class="fas fa-info-circle me-1"></i>Sin productos asociados.
                        </span>
                        @endforelse
                    </td>
                </tr>
                @empty
                <tr>
                    <td colspan="3">
                        <div class="empty-state">
                            <i class="fas fa-database fa-3x mb-3" style="color:#d9b382;"></i>
                            <p>No hay datos de MapReduce disponibles.</p>
                        </div>
                    </td>
                </tr>
                @endforelse
            </tbody>
        </table>
    </div>
</div>

@endif

            @endif
            
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
@if(!empty($predicciones))
const datos = @json($predicciones);

const labels        = datos.map(d => d.nombre);
const consumoMes    = datos.map(d => d.consumo_mes);
const necesidadSem  = datos.map(d => d.necesidad_semana);
const stockActual   = datos.map(d => d.stock_actual);
const maxNecesidad = Math.max(...datos.map(d => d.necesidad_semana));
const coloresAlerta = datos.map(d => {
    const ratio = maxNecesidad > 0 ? d.necesidad_semana / maxNecesidad : 0;
    if (ratio >= 0.66) return 'rgba(220,53,69,0.85)';      // rojo — mucha necesidad
    if (ratio >= 0.33) return 'rgba(255,193,7,0.85)';       // amarillo — media
    return 'rgba(40,167,69,0.85)';                          // verde — poca necesidad
});


// Gráfica de dispersión
new Chart(document.getElementById('graficaDispersion'), {
    type: 'scatter',
    data: {
        datasets: [{
            label: 'Insumos (necesidad vs stock)',
            data: datos.map(d => ({ x: d.necesidad_semana, y: d.stock_actual, nombre: d.nombre })),
            backgroundColor: coloresAlerta,
            pointRadius: 8,
            pointHoverRadius: 12,
        }]
    },
    options: {
        responsive: true,
        plugins: {
            tooltip: {
                callbacks: {
                    label: ctx => `${ctx.raw.nombre} — Necesidad: ${ctx.raw.x.toFixed(3)}, Stock: ${ctx.raw.y.toFixed(3)}`
                }
            }
        },
        scales: {
            x: { title: { display: true, text: 'Necesidad semanal (predicción)' } },
            y: { title: { display: true, text: 'Stock actual' } }
        }
    }
});

@endif

function toggleDetalle() {
    const filas   = document.querySelectorAll('.fila-extra');
    const chevron = document.getElementById('detalleChevron');
    const btn     = document.getElementById('btnVerMas');
    const oculto  = filas.length > 0 && filas[0].style.display === 'none';

    filas.forEach(f => f.style.display = oculto ? '' : 'none');
    chevron.className = oculto ? 'fas fa-chevron-up me-2' : 'fas fa-chevron-down me-2';
    btn.innerHTML = oculto
        ? '<i class="fas fa-chevron-up me-2" id="detalleChevron"></i> Ocultar'
        : '<i class="fas fa-chevron-down me-2" id="detalleChevron"></i> Ver todos los insumos ({{ count($predicciones) - 3 }} más)';
}
document.getElementById('mapreduceCollapse')?.addEventListener('show.bs.collapse', function () {
    document.querySelector('[data-bs-target="#mapreduceCollapse"] i').className = 'fas fa-chevron-up me-1';
    document.querySelector('[data-bs-target="#mapreduceCollapse"]').innerHTML = 
        '<i class="fas fa-chevron-up me-1"></i> Ocultar tabla';
});
document.getElementById('mapreduceCollapse')?.addEventListener('hide.bs.collapse', function () {
    document.querySelector('[data-bs-target="#mapreduceCollapse"]').innerHTML = 
        '<i class="fas fa-chevron-down me-1"></i> Ver tabla';
});

</script>

<style>
.resumen-card.warning i { color:#ffc107; }
.inventario-container { position:relative;min-height:100vh;background:linear-gradient(145deg,#faf0e6,#f5e6d3);font-family:'Poppins','Segoe UI',sans-serif;padding:20px 0;overflow-x:hidden; }
.coffee-elements { position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0; }
.coffee-cup { position:absolute;opacity:.15; }
.cup-1 { top:30px;left:30px;transform:scale(.7); }
.white-cup { background:linear-gradient(145deg,#fff,#f8f8f8) !important; }
.white-handle { border-color:#f0f0f0 !important;border-right:6px solid #fff !important; }
.cup-top { width:60px;height:15px;border-radius:50%;background:linear-gradient(145deg,#fff,#f0f0f0); }
.cup-body { width:50px;height:45px;border-radius:0 0 25px 25px;background:linear-gradient(145deg,#fff,#f5f5f5);top:-7px;position:relative; }
.cup-handle { width:18px;height:30px;border:5px solid #f0f0f0;border-left:none;border-radius:0 15px 15px 0;position:absolute;right:-15px;top:10px; }
.steam { position:absolute;background:rgba(255,255,255,.5);border-radius:50%;animation:steam 3s infinite; }
.s1{width:10px;height:10px;top:-15px;left:15px} .s2{width:8px;height:8px;top:-20px;left:25px;animation-delay:.5s} .s3{width:6px;height:6px;top:-18px;left:35px;animation-delay:1s}
@keyframes steam{0%,100%{transform:translateY(0) scale(1);opacity:.5}50%{transform:translateY(-10px) scale(1.2);opacity:.2}}
.coffee-bean{position:absolute;width:15px;height:7px;background:#8B4513;border-radius:50%;opacity:.1;animation:float 20s infinite linear;transform:rotate(45deg)}
.bean-1{top:15%;left:5%} .bean-2{bottom:20%;right:5%}
@keyframes float{from{transform:translateY(0) rotate(45deg);opacity:.1}to{transform:translateY(-100vh) rotate(405deg);opacity:0}}
.particle{position:absolute;width:3px;height:3px;background:rgba(139,69,19,.2);border-radius:50%;animation:particle-float 15s infinite linear}
.particle-1{top:20%;left:15%}
@keyframes particle-float{from{transform:translateY(0) scale(1);opacity:.3}to{transform:translateY(-100vh) scale(0);opacity:0}}

.inventario-header { background:linear-gradient(135deg,#8B4513,#A0522D);color:white;padding:25px 30px;display:flex;align-items:center;gap:20px;position:relative;overflow:hidden;border-radius:30px 30px 0 0;z-index:10;flex-wrap:wrap; }
.inventario-header::after { content:'';position:absolute;top:0;right:0;width:200px;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.2));transform:skewX(-20deg) translateX(100px);animation:shine 3s infinite; }
@keyframes shine{0%{transform:skewX(-20deg) translateX(100px)}20%{transform:skewX(-20deg) translateX(-200px)}100%{transform:skewX(-20deg) translateX(-200px)}}
.header-icon { width:60px;height:60px;background:rgba(255,255,255,.2);border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:2rem; }
.header-title h4 { margin:0;font-weight:700;font-size:1.5rem; }
.header-title p { margin:5px 0 0;opacity:.9;font-size:.9rem; }
.coffee-decoration-header { margin-left:auto;font-size:1.5rem; }
.coffee-decoration-header span { margin:0 5px;animation:bounce 2s infinite;display:inline-block; }
@keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}

.btn-nuevo { background:rgba(255,255,255,.2);backdrop-filter:blur(5px);color:white;border:1px solid rgba(255,255,255,.3);padding:10px 20px;border-radius:50px;text-decoration:none;font-weight:600;display:inline-flex;align-items:center;transition:all .3s ease; }
.btn-nuevo:hover { background:#D4AF37;border-color:#D4AF37;color:#2c1a0b;transform:translateY(-2px); }

.inventario-card { background:rgba(255,255,255,.98);border-radius:0 0 30px 30px;padding:30px;box-shadow:0 20px 40px rgba(139,69,19,.15);z-index:10;position:relative; }

.inventario-resumen { display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px; }
.resumen-card { background:linear-gradient(145deg,#fff,#f5f0eb);padding:25px;border-radius:20px;text-align:center;box-shadow:0 5px 15px rgba(0,0,0,.05);border:1px solid rgba(139,69,19,.1);transition:all .3s ease; }
.resumen-card:hover { transform:translateY(-5px);box-shadow:0 15px 30px rgba(139,69,19,.15); }
.resumen-card i { font-size:2.5rem;color:#8B4513;margin-bottom:15px; }
.resumen-card.danger i { color:#dc3545; }
.resumen-valor { display:block;font-size:2rem;font-weight:700;color:#3E2723; }
.resumen-label { color:#8B6B4F;font-size:.9rem;text-transform:uppercase;letter-spacing:.5px; }

.chart-wrapper { background:#faf5f0;border-radius:20px;padding:25px;border:1px solid #e8d5c0; }
.chart-title { color:#5D4037;font-weight:700;font-size:1.1rem;margin-bottom:15px; }

.inventario-table { width:100%;border-collapse:separate;border-spacing:0 10px; }
.inventario-table thead th { background:#f8f4f0;color:#5D4037;padding:15px;font-weight:600;border-radius:10px; }
.inventario-table tbody tr { background:white;border-radius:15px;box-shadow:0 3px 10px rgba(0,0,0,.03);transition:all .3s ease; }
.inventario-table tbody tr:hover { transform:translateY(-3px);box-shadow:0 10px 25px rgba(139,69,19,.15); }
.inventario-table tbody td { padding:15px;vertical-align:middle;border:none; }

.tipo-badge { padding:5px 12px;border-radius:20px;font-size:.82rem;font-weight:600; }
.tipo-piezas { background:#e3f2fd;color:#1565c0; }
.tipo-gramos { background:#e8f5e9;color:#2e7d32; }
.tipo-litros { background:#e8eaf6;color:#283593; }
.tipo-kilogramos { background:#fff8e1;color:#f57f17; }
.tipo-mililitros { background:#ede7f6;color:#4527a0; }

.stock-badge { display:inline-block;padding:6px 14px;border-radius:30px;font-weight:600;font-size:.9rem; }
.stock-badge.normal { background:linear-gradient(145deg,#d4edda,#c3e6cb);color:#155724; }
.stock-badge.bajo { background:linear-gradient(145deg,#fff3cd,#ffe69c);color:#856404; }

.badge-estado { display:inline-block;padding:5px 12px;border-radius:20px;font-size:.85rem;font-weight:600; }
.badge-estado.normal { background:#28a745;color:white; }
.badge-estado.agotado { background:#dc3545;color:white; }

.empty-state { text-align:center;padding:40px; }
.propuesta-card { background:white;border-radius:18px;padding:20px 25px;box-shadow:0 3px 12px rgba(0,0,0,.06);border-left:5px solid #e8d5c0;transition:all .3s; }
.propuesta-card:hover { transform:translateY(-3px);box-shadow:0 10px 25px rgba(139,69,19,.12); }
.propuesta-card.nivel-danger  { border-left-color:#dc3545; }
.propuesta-card.nivel-warning { border-left-color:#ffc107; }
.propuesta-card.nivel-info    { border-left-color:#17a2b8; }
.propuesta-card.nivel-success { border-left-color:#28a745; }

.propuesta-header { display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;margin-bottom:12px; }
.propuesta-nombre { display:block;font-weight:700;color:#3E2723;font-size:1.05rem; }
.propuesta-cad    { font-size:.85rem;color:#8B6B4F; }
.propuesta-badge-wrap { display:flex;gap:8px;align-items:center;flex-wrap:wrap; }

.descuento-badge { background:linear-gradient(135deg,#8B4513,#A0522D);color:white;padding:4px 12px;border-radius:20px;font-weight:700;font-size:.85rem; }

.propuestas-lista { background:#faf5f0;border-radius:12px;padding:14px 18px; }
.propuestas-grid  { display:flex;flex-direction:column;gap:8px; }
.propuesta-item   { display:flex;align-items:center;gap:10px;flex-wrap:wrap; }
.prop-producto    { font-weight:600;color:#3E2723;min-width:150px; }
.prop-texto       { color:#5D4037;flex:1; }
.prop-ahorro      { background:linear-gradient(145deg,#d4edda,#c3e6cb);color:#155724;padding:3px 10px;border-radius:20px;font-size:.82rem;font-weight:600; }
.detalle-toggle-header { display:flex;justify-content:space-between;align-items:center;background:#f8f4f0;border:1px solid #e8d5c0;border-radius:15px;padding:16px 22px;cursor:pointer;transition:all .3s;user-select:none; }

#detalleContenido {
    border: 1px solid #e8d5c0;
    border-radius: 0 0 15px 15px;
    padding: 20px;
    background: white;
    margin-bottom: 10px;
}

.btn-ver-mas {
    width: 100%;
    background: #f8f4f0;
    border: 1px solid #e8d5c0;
    border-radius: 0 0 15px 15px;
    padding: 14px;
    color: #8B4513;
    font-weight: 600;
    cursor: pointer;
    transition: all .3s;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20px;
    font-size: .95rem;
}
.btn-ver-mas:hover {
    background: #f0e8dc;
    box-shadow: 0 4px 12px rgba(139,69,19,.1);
}

.mapreduce-ranking-item {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    padding: 6px 0;
    border-bottom: 1px dashed #f0e4d4;
}
.mapreduce-ranking-item:last-child {
    border-bottom: none;
}
.mapreduce-pos {
    background: linear-gradient(135deg, #8B4513, #A0522D);
    color: white;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: .8rem;
    font-weight: 700;
    min-width: 32px;
    text-align: center;
}
.mapreduce-detail {
    color: #8B6B4F;
    font-size: .85rem;
    background: #f8f4f0;
    padding: 2px 10px;
    border-radius: 20px;
    border: 1px solid #e8d5c0;
}
/* ===== Error absoluto: predicción vs real ===== */
.pred-error-cell {
    display: flex;
    flex-direction: column;
    gap: 4px;
    align-items: flex-start;
}
.pred-real, .pred-pred {
    display: flex;
    align-items: center;
    gap: 6px;
}
.pred-label {
    font-size: .72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .4px;
    color: #8B6B4F;
    min-width: 30px;
}
.pred-value {
    font-size: .9rem;
    color: #5D4037;
    font-weight: 600;
}
.error-delta {
    font-size: .78rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    letter-spacing: .3px;
}
.error-ok   { background: #d4edda; color: #155724; }
.error-warn { background: #fff3cd; color: #856404; }
.error-bad  { background: #f8d7da; color: #721c24; }
.error-na { background: #e9ecef; color: #6c757d; }

</style>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">

@endsection
