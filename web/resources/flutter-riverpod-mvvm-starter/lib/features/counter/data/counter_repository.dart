import 'package:flutter_riverpod/flutter_riverpod.dart';

final counterRepositoryProvider = Provider<CounterRepository>(
  (ref) => const CounterRepository(),
);

class CounterRepository {
  const CounterRepository();

  int get initialValue => 0;

  int adjust(int current, int amount) => current + amount;
}
