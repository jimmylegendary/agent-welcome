import 'package:go_router/go_router.dart';

import '../features/counter/view/counter_screen.dart';

final appRouter = GoRouter(
  routes: [
    GoRoute(path: '/', builder: (context, state) => const CounterScreen()),
  ],
);
