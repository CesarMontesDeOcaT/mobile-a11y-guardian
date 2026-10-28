# Mobile Accessibility - WCAG 2.2 AA (Focus & Traversal)

Este documento define las reglas normativas de accesibilidad móvil aplicables a la orquestación de lectores de pantalla (TalkBack/VoiceOver).

## WCAG 2.4.3: Focus Order (Orden del Foco)
**Definición oficial:** Si una página o pantalla puede ser navegada secuencialmente y la secuencia de navegación afecta su significado o su operación, los componentes enfocables reciben el foco en un orden que preserva el significado y la operabilidad.

**Aplicación en Jetpack Compose (Layout Traversal):**
*   **El Problema (Fragmentación):** Los lectores de pantalla en móviles leen la pantalla mediante deslizamientos (swipes). Si un contenedor lógico (como una tarjeta de producto, un elemento de lista o una fila de perfil de usuario) está compuesto por múltiples textos e iconos, TalkBack atrapará al usuario obligándolo a hacer múltiples swipes para leer información que debería ser un solo bloque. Esto viola el orden de foco lógico y frustra al usuario.
*   **La Solución (Merge Semantics):** Los componentes visuales que actúan como una unidad semántica o de interacción única **DEBEN** agrupar a sus hijos semánticos. En Compose, esto se logra aplicando `Modifier.semantics(mergeDescendants = true)` al contenedor padre (`Card`, `Row`, `Column`).

## Reglas de Evaluación para la IA
1.  **Unidad Lógica:** Si los textos dentro de un layout no tienen sentido útil por sí solos de forma aislada, o si obligan a un sobreesfuerzo de swipes, deben unificarse.
2.  **Clicabilidad:** Si un contenedor padre es interactivo (`clickable`, `combinedClickable`, `toggleable`), sus hijos legibles internos deben estar fusionados para que el anuncio de la acción englobe el contexto del contenido.
3.  **Justificación de Hallazgos:** Cada vez que detectes un contenedor fragmentado, clasifícalo como una violación del **criterio WCAG 2.4.3 (Focus Order)** en tu reporte.