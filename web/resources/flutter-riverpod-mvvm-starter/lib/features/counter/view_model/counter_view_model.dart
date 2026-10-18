import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/counter_repository.dart';

final counterViewModelProvider = NotifierProvider<CounterViewModel, int>(
  CounterViewModel.new,
);

class CounterViewModel extends Notifier<int> {
  late CounterRepository _repository;

  @override
  int build() {
    _repository = ref.watch(counterRepositoryProvider);
    return _repository.initialValue;
  }

  void increment() {
    state = _repository.adjust(state, 1);
  }

  void decrement() {
    state = _repository.adjust(state, -1);
  }
}
