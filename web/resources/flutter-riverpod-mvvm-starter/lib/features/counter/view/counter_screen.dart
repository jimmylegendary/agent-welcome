import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../view_model/counter_view_model.dart';

class CounterScreen extends ConsumerWidget {
  const CounterScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(counterViewModelProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('MVVM counter')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Repository → ViewModel → View'),
            const SizedBox(height: 12),
            Text('$count', style: Theme.of(context).textTheme.displayMedium),
            const SizedBox(height: 16),
            Wrap(
              spacing: 12,
              children: [
                OutlinedButton(
                  onPressed: ref
                      .read(counterViewModelProvider.notifier)
                      .decrement,
                  child: const Text('−1'),
                ),
                FilledButton(
                  onPressed: ref
                      .read(counterViewModelProvider.notifier)
                      .increment,
                  child: const Text('+1'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
