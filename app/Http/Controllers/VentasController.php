<?php
// app/Http/Controllers/VentasController.php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Venta;
use App\Models\Producto;
use App\Models\Inventario;
use Illuminate\Support\Facades\DB;

class VentasController extends Controller
{
    public function __construct()
    {
        $this->middleware('auth:usuarios');
    }

    public function index()
    {
        $user = auth()->guard('usuarios')->user();
        $ventas = Venta::orderBy('created_at', 'desc')->paginate(15);
        
        return view('ventas.index', compact('ventas', 'user'));
    }

    public function show($id)
    {
        $user = auth()->guard('usuarios')->user();
        $venta = Venta::find($id);
        
        if (!$venta) {
            return redirect()->route('ventas.index')->with('error', 'Venta no encontrada');
        }
        
        return view('ventas.show', compact('venta', 'user'));
    }

    public function mesasDisponibles()
    {
        // Obtener mesas ocupadas en las últimas 2 horas
        $mesasOcupadas = Venta::where('created_at', '>=', now()->subHours(2))
            ->where('estado', '!=', 'completada')
            ->pluck('mesa')
            ->toArray();

        $mesas = [];
        for ($i = 1; $i <= 10; $i++) {
            $mesas[] = [
                'numero' => $i,
                'disponible' => !in_array($i, $mesasOcupadas)
            ];
        }

        return response()->json($mesas);
    }



public function reportes()
{
    $user = auth()->guard('usuarios')->user();

    // Ventas del día
    $ventasHoy = Venta::whereDate('created_at', today())->get();
    $totalHoy  = $ventasHoy->sum('total');

    // Productos más vendidos
    $productosVendidos = [];
    foreach ($ventasHoy as $venta) {
        foreach ($venta->productos as $producto) {
            $nombre = $producto['nombre'];
            $productosVendidos[$nombre] = ($productosVendidos[$nombre] ?? 0) + $producto['cantidad'];
        }
    }
    arsort($productosVendidos);
    $masVendidos = array_slice($productosVendidos, 0, 5, true);

    // ML: estadísticas del modelo
    $pythonApi   = app(\App\Services\PythonApiService::class);
    $mlResponse  = $pythonApi->getMLEstadisticas();
    $mlStats     = $mlResponse['success'] ? $mlResponse['data'] : null;

    $clientesResponse = $pythonApi->getClientesFrecuentes();
    $clientesFrecuentes = $clientesResponse['success'] ? $clientesResponse['data'] : [];

    $productosMesResponse = $pythonApi->getProductosMes();
    $productosMes = $productosMesResponse['success'] ? $productosMesResponse['data'] : [];

    $prediccionResponse = $pythonApi->getPrediccionSemana();
    $prediccionSemana = $prediccionResponse['success'] ? $prediccionResponse['data'] : null;
    $pathCombos = base_path('api/kmeans_productos.json');

    $combos = [];

if (file_exists($pathCombos)) {
    $combos = json_decode(file_get_contents($pathCombos), true) ?? [];
}
    // Segmentación de clientes: PCA + WCSS
    $pathPca  = base_path('api/segmentacion_pca.json');
    $pathWcss = base_path('api/segmentacion_wcss.json');

    $segmentacionPca  = file_exists($pathPca)  ? json_decode(file_get_contents($pathPca),  true) ?? [] : [];
    $segmentacionWcss = file_exists($pathWcss) ? json_decode(file_get_contents($pathWcss), true) ?? [] : [];

    // ── Etiquetado de segmentos por reglas sobre features reales ──────────
    $definiciones = [
        'vip'      => ['icono' => '🏆', 'etiqueta' => 'Cliente VIP',               'color' => '#92670a', 'bg' => '#fffbec', 'border' => '#D4AF37', 'accion' => 'Programa de lealtad exclusivo con beneficios mensuales'],
        'mananero' => ['icono' => '☕', 'etiqueta' => 'Amante del café mañanero',   'color' => '#2e7d32', 'bg' => '#e8f5e9', 'border' => '#81c784', 'accion' => 'Oferta 2x1 en bebidas de 7–10 AM entre semana'],
        'finde'    => ['icono' => '📅', 'etiqueta' => 'Comprador de fin de semana', 'color' => '#e65100', 'bg' => '#fff3e0', 'border' => '#ffb74d', 'accion' => 'Promociones especiales sábado y domingo'],
        'dormido'  => ['icono' => '💤', 'etiqueta' => 'Cliente dormido',            'color' => '#5a5a5a', 'bg' => '#f4f4f4', 'border' => '#bdbdbd', 'accion' => 'Campaña de reactivación con cupón del 20%'],
        'regular'  => ['icono' => '⭐', 'etiqueta' => 'Cliente regular',            'color' => '#1565c0', 'bg' => '#e8f4fd', 'border' => '#90caf9', 'accion' => 'Tarjeta de puntos para incentivar frecuencia'],
    ];

    $segmentosEtiquetados = [];

    if (!empty($segmentacionWcss['clientes'])) {
        foreach ($segmentacionWcss['clientes'] as $cli) {
            $frecuencia = $cli['frecuencia']      ?? 0;
            $gasto      = $cli['gasto_total']     ?? 0;
            $recencia   = $cli['recencia_dias']   ?? 999;
            $hora       = $cli['hora_preferida']  ?? 12;
            $pctFinde   = $cli['pct_fines_semana'] ?? 0;
            $ticket     = $cli['ticket_promedio'] ?? 0;

            if ($frecuencia >= 20 || ($frecuencia >= 5 && $gasto >= 5000)) {
                $tipo = 'vip';
            } elseif ($recencia > 60) {
                $tipo = 'dormido';
            } elseif ($pctFinde >= 0.5 && $frecuencia < 10) {
                $tipo = 'finde';
            } elseif ($hora <= 10 && $frecuencia >= 3) {
                $tipo = 'mananero';
            } else {
                $tipo = 'regular';
            }

            if (!isset($segmentosEtiquetados[$tipo])) {
                $segmentosEtiquetados[$tipo] = array_merge($definiciones[$tipo], ['clientes' => []]);
            }
            $segmentosEtiquetados[$tipo]['clientes'][] = [
                'nombre'        => $cli['nombre'],
                'frecuencia'    => $frecuencia,
                'gasto_total'   => $gasto,
                'ticket'        => $ticket,
                'recencia_dias' => $recencia,
                'hora'          => round($hora, 1),
            ];
        }

        // Orden fijo de presentación
        $segmentosOrdenados = [];
        foreach (array_keys($definiciones) as $k) {
            if (isset($segmentosEtiquetados[$k])) {
                $segmentosOrdenados[$k] = $segmentosEtiquetados[$k];
            }
        }
        $segmentosEtiquetados = $segmentosOrdenados;
    }

    return view('ventas.reportes', compact(
        'user', 'ventasHoy', 'totalHoy', 'masVendidos', 'mlStats',
        'clientesFrecuentes', 'productosMes', 'prediccionSemana', 'combos',
        'segmentacionPca', 'segmentacionWcss', 'segmentosEtiquetados'
    ));
}

public function predecir(Request $request)
{
    $request->validate([
        'cantidad' => 'required|numeric|min:1',
        'precio'   => 'required|numeric|min:1',
    ]);

    $pythonApi = app(\App\Services\PythonApiService::class);
    $resultado = $pythonApi->predecirVenta($request->cantidad, $request->precio);

    return response()->json($resultado);
}

}